from datetime import date
from typing import Literal

from pydantic import BaseModel

DayState = Literal["none", "partial", "most", "all", "rest", "future"]


class CalendarDay(BaseModel):
    business_date: date
    expected_count: int
    done_count: int
    state: DayState
    # R9: a day written later is visible as such, never disguised as prompt.
    backfilled_count: int = 0
    # Whether this day is still inside the seven-day window; the client shows
    # the backfill form from this flag rather than re-deriving the rule.
    can_backfill: bool = False


class CalendarView(BaseModel):
    month: str
    today: date
    # ISO weekday (1 = Monday) of the first day in the month, so the client
    # never has to parse dates to lay out the grid.
    first_weekday: int
    days: list[CalendarDay]
