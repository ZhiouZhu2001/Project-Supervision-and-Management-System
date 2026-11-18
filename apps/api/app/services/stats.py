"""Rates, a twelve-week rollup and a thirty-day count.

Every number here is derived from the same expected-day list the streak uses,
so the statistics page and the calendar cannot disagree about what was owed.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.project import Project
from app.services.schedule import load_rules
from app.services.status import load_status_rules
from app.services.streak import current_streak, longest_streak, window_start
from app.services.streak_inputs import expected_days_for, load_logged_days

ROLLUP_WEEKS = 12
RECENT_DAYS = 30


@dataclass
class ProjectRates:
    project: Project
    expected: int
    recorded: int
    clean: int
    current_streak: int
    longest_streak: int

    @property
    def completion_rate(self) -> float | None:
        return None if self.expected == 0 else round(self.recorded / self.expected, 4)

    @property
    def clean_completion_rate(self) -> float | None:
        return None if self.expected == 0 else round(self.clean / self.expected, 4)


@dataclass
class WeekBucket:
    week_start: date
    expected: int
    recorded: int


@dataclass
class Statistics:
    projects: list[ProjectRates]
    rollup: list[WeekBucket]
    recent_logs: int


def week_start(day: date) -> date:
    """Monday of the ISO week containing `day`."""
    return day - timedelta(days=day.isoweekday() - 1)


async def build_statistics(db: AsyncSession, *, current: date) -> Statistics:
    projects = list(
        await db.scalars(
            select(Project)
            .where(Project.deleted_at.is_(None), Project.status != "archived")
            .order_by(Project.sort_order, Project.created_at)
        )
    )

    start = window_start(current)
    global_rules, by_project = await load_rules(db, until=current)
    status_rules = await load_status_rules(db, until=current)
    recorded_any = await load_logged_days(db, start=start, end=current, include_backfilled=True)
    recorded_clean = await load_logged_days(db, start=start, end=current, include_backfilled=False)

    rates: list[ProjectRates] = []
    rollup_start = week_start(current) - timedelta(weeks=ROLLUP_WEEKS - 1)
    buckets: dict[date, list[int]] = {}

    for project in projects:
        days = expected_days_for(
            project,
            current=current,
            global_rules=global_rules,
            overrides=by_project.get(project.id, []),
            history=status_rules.get(project.id, []),
        )
        any_days = recorded_any.get(project.id, set())
        clean_days = recorded_clean.get(project.id, set())

        rated = [day for day in days if day >= rollup_start] or days
        rates.append(
            ProjectRates(
                project=project,
                expected=len(rated),
                recorded=sum(1 for day in rated if day in any_days),
                clean=sum(1 for day in rated if day in clean_days),
                current_streak=current_streak(days, clean_days, current),
                longest_streak=longest_streak(days, clean_days),
            )
        )

        for day in days:
            if day < rollup_start:
                continue
            bucket = buckets.setdefault(week_start(day), [0, 0])
            bucket[0] += 1
            if day in any_days:
                bucket[1] += 1

    rollup = [
        WeekBucket(week_start=week, expected=counts[0], recorded=counts[1])
        for week, counts in sorted(buckets.items())
        # A week nobody expected anything is not a zero, it is absent.
        if counts[0] > 0
    ]

    recent = (
        await db.scalar(
            select(func.count())
            .select_from(Log)
            .where(
                Log.deleted_at.is_(None),
                Log.business_date >= current - timedelta(days=RECENT_DAYS - 1),
                Log.business_date <= current,
            )
        )
    ) or 0

    return Statistics(projects=rates, rollup=rollup, recent_logs=recent)
