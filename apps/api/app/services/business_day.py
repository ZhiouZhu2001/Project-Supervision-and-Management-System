"""The one place that decides what "today" means.

A business day is `[04:00, next 04:00)` in Europe/Madrid. Its date is the
calendar date of the starting instant, so something written at 02:00 belongs
to yesterday. See ADR 0003.

Nothing outside this module is allowed to compute a business day.
"""

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.clock import now_utc

MADRID = ZoneInfo("Europe/Madrid")
DAY_CUTOVER_HOUR = 4


class BusinessDateError(ValueError):
    """A business date the rules do not allow.

    Carries a stable code so routers can translate it into the standard error
    body without importing this module's semantics into the HTTP layer.
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


def business_date_for(instant: datetime) -> date:
    """UTC instant -> business day."""
    local = instant.astimezone(MADRID)
    return (local - timedelta(hours=DAY_CUTOVER_HOUR)).date()


def business_day_bounds(day: date) -> tuple[datetime, datetime]:
    """Business day -> [start, end) in UTC. Length varies 23-25 hours on DST days."""
    start_local = datetime.combine(day, time(DAY_CUTOVER_HOUR), tzinfo=MADRID)
    end_local = datetime.combine(day + timedelta(days=1), time(DAY_CUTOVER_HOUR), tzinfo=MADRID)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def today_business_date() -> date:
    return business_date_for(now_utc())


def validate_business_date(value: date, *, today: date | None = None) -> date:
    """Reject dates that cannot be recorded.

    The future is the only check that belongs to every caller; the seven-day
    backfill window (R9) is a rule about logs and is applied where logs are
    written. `today` is injectable so tests do not depend on the wall clock.
    """
    current = today if today is not None else today_business_date()
    if value > current:
        raise BusinessDateError(
            "BUSINESS_DATE_IN_FUTURE",
            "A business date cannot be in the future",
        )
    return value
