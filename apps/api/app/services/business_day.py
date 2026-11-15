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
