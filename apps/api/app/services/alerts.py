"""The email that makes the system impossible to ignore (R12).

One message, naming the projects that were expected today and were not
recorded, with the numbers that make ignoring them feel like a choice.
"""

import asyncio
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import AlertLog
from app.models.project import Project
from app.services.schedule import load_rules
from app.services.status import load_status_rules
from app.services.streak import consecutive_misses, current_streak
from app.services.streak_inputs import expected_days_for, load_logged_days


@dataclass
class MissEntry:
    project_id: UUID
    name: str
    streak: int
    missed_days: int
    url: str


@dataclass
class AlertReport:
    business_date: date
    status: str  # sent | no_misses | failed | skipped
    project_count: int = 0
    detail: str | None = None
    attempts: int = 0


# R12: three attempts with exponential backoff, then give up. The delay is a
# parameter of run_digest so tests do not sleep through it.
ATTEMPTS = 3
BACKOFF_SECONDS = 2.0


async def collect_misses(db: AsyncSession, *, current: date, base_url: str) -> list[MissEntry]:
    """Active projects that owed a record today and do not have one."""
    projects = list(
        await db.scalars(
            select(Project)
            .where(Project.deleted_at.is_(None), Project.status == "active")
            .order_by(Project.sort_order, Project.created_at)
        )
    )
    if not projects:
        return []

    global_rules, by_project = await load_rules(db, until=current)
    status_rules = await load_status_rules(db, until=current)
    # Everything the projects ever had, not a bounded window: "consecutive
    # missed days" and the longest streak both reach back past any cap (R6).
    start = min((project.counting_from for project in projects), default=current)
    logged = await load_logged_days(db, start=start, end=current, include_backfilled=True)
    clean = await load_logged_days(db, start=start, end=current, include_backfilled=False)

    entries: list[MissEntry] = []
    for project in projects:
        days = expected_days_for(
            project,
            current=current,
            global_rules=global_rules,
            overrides=by_project.get(project.id, []),
            history=status_rules.get(project.id, []),
        )
        # Not expected today (rest day, pause, before it started): no alert.
        if current not in days:
            continue
        project_logs = logged.get(project.id, set())
        if current in project_logs:
            continue

        # Invariant 3: the run of misses is a streak fact, not a digest fact.
        missed = consecutive_misses(days, project_logs)

        entries.append(
            MissEntry(
                project_id=project.id,
                name=project.name,
                streak=current_streak(days, clean.get(project.id, set()), current),
                missed_days=missed,
                url=f"{base_url.rstrip('/')}/projects/{project.id}",
            )
        )

    return entries


def render_digest(entries: list[MissEntry], *, current: date) -> tuple[str, str]:
    count = len(entries)
    subject = (
        f"Daymark: {entries[0].name} still needs a record today"
        if count == 1
        else f"Daymark: {count} projects still need a record today"
    )

    lines = [f"Nothing has been written for {current} yet.", ""]
    for entry in entries:
        streak = "no streak yet" if entry.streak == 0 else f"{entry.streak} day streak"
        missed = (
            "first missed day" if entry.missed_days <= 1 else f"{entry.missed_days} days in a row"
        )
        lines.append(f"- {entry.name} Ã¢â‚¬â€ {streak}, {missed}")
        lines.append(f"  {entry.url}")

    lines += [
        "",
        "The day closes at 04:00. A few words is enough.",
    ]
    return subject, "\n".join(lines)


async def last_judged_business_date(db: AsyncSession) -> date | None:
    rows = await db.scalars(select(AlertLog.business_date).order_by(AlertLog.business_date.desc()))
    return rows.first()


async def run_digest(
    db: AsyncSession,
    mailer,
    *,
    to: str,
    current: date,
    base_url: str,
    backoff_seconds: float = BACKOFF_SECONDS,
) -> AlertReport:
    """Send at most one digest per business day (invariant 6, R12).

    Idempotency by pre-emption, not by check-then-act (ARCH 5.5): the unique
    insert is the lock. Two overlapping runs both see "no row yet" in a read,
    so a read-first design sends twice; here one insert wins and the loser
    returns without sending.
    """
    alert_id = await _claim_business_day(db, current)
    if alert_id is None:
        existing = await db.scalar(select(AlertLog).where(AlertLog.business_date == current))
        return AlertReport(
            business_date=current,
            status="skipped",
            project_count=existing.project_count if existing is not None else 0,
            detail=f"already judged ({existing.status if existing is not None else 'unknown'})",
        )

    entries = await collect_misses(db, current=current, base_url=base_url)

    if not entries:
        await _finish(db, alert_id, status="no_misses", project_count=0, detail=None)
        return AlertReport(business_date=current, status="no_misses")

    subject, body = render_digest(entries, current=current)
    error, attempts = await _send_with_retries(
        mailer, to=to, subject=subject, body=body, backoff_seconds=backoff_seconds
    )

    if error is not None:
        await _finish(db, alert_id, status="failed", project_count=len(entries), detail=error)
        return AlertReport(
            business_date=current,
            status="failed",
            project_count=len(entries),
            detail=error,
            attempts=attempts,
        )

    await _finish(db, alert_id, status="sent", project_count=len(entries), detail=None)
    return AlertReport(
        business_date=current, status="sent", project_count=len(entries), attempts=attempts
    )


async def _claim_business_day(db: AsyncSession, current: date) -> UUID | None:
    """Insert this day's judgement row, or return None if it already exists.

    Committed immediately: the row has to be visible to (and conflicting with)
    any other run before the slow part Ã¢â‚¬â€ reading logs, sending mail Ã¢â‚¬â€ starts.
    A crash after this point leaves the day marked `pending`, which is the
    honest record that a digest was started and its outcome unknown; retrying
    it automatically would risk the double-send invariant 6 exists to prevent.
    """
    alert_id = await db.scalar(
        insert(AlertLog)
        .values(business_date=current, status="pending", project_count=0)
        .on_conflict_do_nothing(index_elements=[AlertLog.business_date])
        .returning(AlertLog.id)
    )
    await db.commit()
    return alert_id


async def _finish(
    db: AsyncSession, alert_id: UUID, *, status: str, project_count: int, detail: str | None
) -> None:
    await db.execute(
        update(AlertLog)
        .where(AlertLog.id == alert_id)
        .values(status=status, project_count=project_count, detail=detail)
    )
    await db.commit()


async def _send_with_retries(
    mailer, *, to: str, subject: str, body: str, backoff_seconds: float
) -> tuple[str | None, int]:
    """R12: three attempts with exponential backoff, then give up quietly.

    Returns the last error (None on success) and the number of attempts made.
    A digest failure must never raise into the scheduler: the owner not being
    emailed twice is bad, the whole job dying is worse.
    """
    error: str | None = None
    for attempt in range(1, ATTEMPTS + 1):
        try:
            # SMTP is blocking; the event loop must not wait on a mail server.
            await asyncio.to_thread(mailer.send, to=to, subject=subject, body=body)
            return None, attempt
        except Exception as exc:
            error = str(exc)[:1000] or exc.__class__.__name__
            if attempt < ATTEMPTS:
                await asyncio.sleep(backoff_seconds * 2 ** (attempt - 1))
    return error, ATTEMPTS



