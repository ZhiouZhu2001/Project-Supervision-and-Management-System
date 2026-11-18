"""The email that makes the system impossible to ignore (R12).

One message, naming the projects that were expected today and were not
recorded, with the numbers that make ignoring them feel like a choice.
"""

import asyncio
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import AlertLog
from app.models.project import Project
from app.services.schedule import load_rules
from app.services.status import load_status_rules
from app.services.streak import current_streak, window_start
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
    # The whole streak window, not just today: "consecutive missed days" and
    # the streak itself are both computed from past days.
    start = window_start(current)
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

        missed = 0
        for day in reversed(days):
            if day in project_logs:
                break
            missed += 1

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
        lines.append(f"- {entry.name} — {streak}, {missed}")
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
) -> AlertReport:
    """Send at most one digest per business day (invariant 6)."""
    existing = await db.scalar(select(AlertLog).where(AlertLog.business_date == current))
    if existing is not None:
        return AlertReport(
            business_date=current,
            status="skipped",
            project_count=existing.project_count,
            detail=f"already judged ({existing.status})",
        )

    entries = await collect_misses(db, current=current, base_url=base_url)

    if not entries:
        db.add(AlertLog(business_date=current, status="no_misses", project_count=0))
        await db.commit()
        return AlertReport(business_date=current, status="no_misses")

    subject, body = render_digest(entries, current=current)
    try:
        # SMTP is blocking; the event loop must not wait on a mail server.
        await asyncio.to_thread(mailer.send, to=to, subject=subject, body=body)
    except Exception as exc:
        detail = str(exc)[:1000] or exc.__class__.__name__
        db.add(
            AlertLog(
                business_date=current,
                status="failed",
                project_count=len(entries),
                detail=detail,
            )
        )
        await db.commit()
        return AlertReport(
            business_date=current, status="failed", project_count=len(entries), detail=detail
        )

    db.add(AlertLog(business_date=current, status="sent", project_count=len(entries), detail=None))
    await db.commit()
    return AlertReport(business_date=current, status="sent", project_count=len(entries))
