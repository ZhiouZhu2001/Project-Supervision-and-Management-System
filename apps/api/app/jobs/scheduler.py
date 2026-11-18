"""In-process scheduling for the evening digest (R12, invariant 8).

One worker, one scheduler: the process that serves requests is the process
that sends the email, so there is no lock to acquire and no second sender to
race. The catch-up on startup is what makes a restart across 21:00 harmless.
"""

import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.clock import now_utc
from app.models.alert import AlertLog
from app.services.alerts import run_digest
from app.services.business_day import MADRID, today_business_date

logger = logging.getLogger("app.scheduler")

ALERT_HOUR = 21
JOB_ID = "alert-digest"


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
    """Judge today if 21:00 has passed and nobody judged it yet.

    Returns True when a digest was attempted. The `at` parameter exists so the
    behaviour can be tested without waiting for the evening.
    """
    local = (at or now_utc()).astimezone(MADRID)
    if local.hour < ALERT_HOUR:
        return False

    async with session_factory() as session:
        existing = await session.scalar(
            select(AlertLog).where(AlertLog.business_date == today_business_date())
        )
        if existing is not None:
            return False

    await run_alert_job(session_factory=session_factory, mailer=mailer, to=to, base_url=base_url)
    return True


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
