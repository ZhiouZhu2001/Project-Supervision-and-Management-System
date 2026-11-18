from datetime import date
from uuid import UUID

from pydantic import BaseModel


class ProjectRatesView(BaseModel):
    id: UUID
    name: str
    status: str
    expected_days: int
    recorded_days: int
    clean_days: int
    # None means "no expected days yet", which the client renders as a dash.
    # A rate of 0.0 would claim the owner failed at something never asked.
    completion_rate: float | None
    clean_completion_rate: float | None
    current_streak: int
    longest_streak: int


class WeekBucketView(BaseModel):
    week_start: date
    expected: int
    recorded: int


class StatisticsView(BaseModel):
    business_date: date
    projects: list[ProjectRatesView]
    rollup: list[WeekBucketView]
    recent_logs: int
    rollup_weeks: int
    recent_days: int
