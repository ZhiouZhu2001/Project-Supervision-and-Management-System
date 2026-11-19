"""In-process scheduling for the evening digest (R12, invariant 8).

One worker, one scheduler: the process that serves requests is the process
that sends the email, so there is no lock to acquire and no second sender to
race. The catch-up on startup is what makes a restart across 21:00 harmless.
"""

import logging
from datetime import datetime, time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.clock import now_utc
from app.jobs.purge import purge_expired
from app.services.alerts import run_digest
from app.services.business_day import MADRID, business_date_for, today_business_date

logger = logging.getLogger("app.scheduler")

ALERT_HOUR = 21
JOB_ID = "alert-digest"

# 03:15 Madrid: the purge runs before the 03:30 backup, so a backup never
# captures rows that were already due to disappear that night.
PURGE_HOUR = 3
PURGE_MINUTE = 15
PURGE_JOB_ID = "retention-purge"


async def run_alert_job(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    mailer,
    to: str,
    base_url: str,
) -> None:
    async with session_factory() as session:
        report = await run_digest(
            session,
            mailer,
            to=to,
            current=today_business_date(),
            base_url=base_url,
        )
    logger.info(
        "alert digest for %s: %s (%s projects)",
        report.business_date,
        report.status,
        report.project_count,
    )


async def catch_up(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    mailer,
    to: str,
    base_url: str,
    at: datetime | None = None,
) -> bool:
    """Judge the current business day once 21:00 has passed for it.

    Returns True when this call attempted a digest. The target is the current
    *business* day, whose 21:00 may have been yesterday evening: at 01:00 the
    business day is still the previous calendar date, and its cut-off has
    passed. Comparing the wall clock's hour instead would leave that day
    unjudged until the next evening.

    No "has it been judged?" query here — `run_digest` decides that by winning
    the unique insert, so the answer cannot go stale between check and send.
    """
    instant = at or now_utc()
    local = instant.astimezone(MADRID)
    target = business_date_for(instant)
    cut_off = datetime.combine(target, time(ALERT_HOUR), tzinfo=MADRID)
    if local < cut_off:
        return False

    async with session_factory() as session:
        report = await run_digest(session, mailer, to=to, current=target, base_url=base_url)
    return report.status != "skipped"


async def run_purge_job(*, session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Physically remove what was soft-deleted more than thirty days ago.

    Scheduled rather than left to `python -m app.jobs.purge`: a job nobody runs
    is not retention, it is an ever-growing table (AGENTS data conventions).
    """
    async with session_factory() as session:
        report = await purge_expired(session)
    logger.info(
        "retention purge: %s projects, %s logs, %s files",
        report.projects,
        report.logs,
        report.files,
    )


def build_scheduler(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    mailer,
    to: str,
    base_url: str,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=MADRID)

    async def job() -> None:
        await run_alert_job(
            session_factory=session_factory, mailer=mailer, to=to, base_url=base_url
        )

    async def purge() -> None:
        await run_purge_job(session_factory=session_factory)

    scheduler.add_job(
        purge,
        CronTrigger(hour=PURGE_HOUR, minute=PURGE_MINUTE, timezone=MADRID),
        id=PURGE_JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )

    scheduler.add_job(
        job,
        # Explicit timezone on the trigger: the server may run in UTC, and
        # "21:00" must mean 21:00 in Madrid, not on the host.
        CronTrigger(hour=ALERT_HOUR, minute=0, timezone=MADRID),
        id=JOB_ID,
        replace_existing=True,
        # One run at a time, and a missed run is coalesced into one rather
        # than replayed as a burst after a restart.
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    return scheduler
