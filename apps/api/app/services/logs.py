"""Which business day a new log may be written on (R3, R9, invariant 4).

Three rules decide it, and they are the same three every writer needs — the
quick-log form, the calendar's backfill, and anything a later client adds:

* the date must not be in the future, and not older than the backfill window;
* it must not precede `counting_from`, or it would record a day the project
  did not exist (R3);
* a backfilled day accepts at most `BACKFILL_MAX_PER_DAY` backfilled logs.

They lived in the router, which made the router the only place that knew them.
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.project import Project
from app.services.business_day import (
    BACKFILL_MAX_PER_DAY,
    BusinessDateError,
    validate_backfill_window,
    validate_business_date,
)


class BackfillLimitReached(Exception):
    """The project already has its backfilled logs for that day (invariant 4)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass
class LogDay:
    """The validated day, plus the flag the server — not the client — decides."""

    business_date: date
    backfilled: bool


async def backfilled_count(db: AsyncSession, project_id: UUID, business_date: date) -> int:
    """Backfilled, undeleted logs this project already has on that day."""
    return (
        await db.scalar(
            select(func.count())
            .select_from(Log)
            .where(
                Log.project_id == project_id,
                Log.business_date == business_date,
                Log.backfilled.is_(True),
                Log.deleted_at.is_(None),
            )
        )
    ) or 0


async def resolve_log_day(
    db: AsyncSession,
    *,
    project: Project,
    requested: date | None,
    today: date,
) -> LogDay:
    """Validate the requested day and derive `backfilled` (invariants 1 and 2).

    Raises BusinessDateError for a date the app refuses, and
    BackfillLimitReached when the day is already full.
    """
    business_date = requested or today

    validate_business_date(business_date, today=today)
    validate_backfill_window(business_date, today=today)

    if business_date < project.counting_from:
        raise BusinessDateError(
            "BUSINESS_DATE_BEFORE_PROJECT_START",
            "A log cannot predate the day the project started counting",
        )

    # R9: derived from the date, never supplied by the client.
    backfilled = business_date < today
    if backfilled and await backfilled_count(db, project.id, business_date) >= (
        BACKFILL_MAX_PER_DAY
    ):
        raise BackfillLimitReached(
            f"At most {BACKFILL_MAX_PER_DAY} backfilled logs per project per business day"
        )

    return LogDay(business_date=business_date, backfilled=backfilled)
