"""Assemble the inputs a streak needs, once, for every caller.

The rule itself lives in `streak.py` (invariant 3). This module is the only
place that decides *which* days are expected and which count as recorded, so
the today screen and a project's statistics cannot drift apart.
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import Log
from app.models.project import Project
from app.services.schedule import DEFAULT_REST_WEEKDAYS, rest_weekdays_for
from app.services.status import load_status_rules, status_on
from app.services.streak import current_streak, expected_days, longest_streak, window_start


@dataclass
class StreakPair:
    current: int
    longest: int


async def load_logged_days(
    db: AsyncSession, *, start: date, end: date, include_backfilled: bool
) -> dict[UUID, set[date]]:
    """Days with at least one log in the range.

    `include_backfilled=False` gives the days written while the day was still
    running, which is what a streak and a "clean" rate mean (R9).
    """
    conditions = [
        Log.deleted_at.is_(None),
        Log.business_date >= start,
        Log.business_date <= end,
    ]
    if not include_backfilled:
        conditions.append(Log.backfilled.is_(False))

    rows = await db.execute(select(Log.project_id, Log.business_date).where(*conditions).distinct())
    days: dict[UUID, set[date]] = {}
    for project_id, business_date in rows:
        days.setdefault(project_id, set()).add(business_date)
    return days


async def load_checked_days(db: AsyncSession, *, start: date, end: date) -> dict[UUID, set[date]]:
    """Days that count for a streak: written on the day, never backfilled.

    R9: a backfilled log never repairs a streak, so it is not a checked day.
    """
    return await load_logged_days(db, start=start, end=end, include_backfilled=False)


def expected_days_for(
    project: Project,
    *,
    current: date,
    global_rules,
    overrides,
    history,
) -> list[date]:
    """Days this project was expected to be recorded on, ascending.

    Rest days and days on which the project was not active are absent rather
    than "missed", which is what lets a streak close over a pause (R14).
    """
    start = max(project.counting_from, window_start(current))

    def rest_on(day: date) -> frozenset[int]:
        base = rest_weekdays_for(day, global_rules, DEFAULT_REST_WEEKDAYS)
        return rest_weekdays_for(day, overrides, base)

    return [
        day
        for day in expected_days(start, current, rest_for=rest_on)
        if status_on(day, history) == "active"
    ]


async def streaks_for(
    db: AsyncSession, projects: list[Project], *, current: date
) -> dict[UUID, StreakPair]:
    from app.services.schedule import load_rules

    global_rules, by_project = await load_rules(db, until=current)
    status_rules = await load_status_rules(db, until=current)
    checked = await load_checked_days(db, start=window_start(current), end=current)

    result: dict[UUID, StreakPair] = {}
    for project in projects:
        days = expected_days_for(
            project,
            current=current,
            global_rules=global_rules,
            overrides=by_project.get(project.id, []),
            history=status_rules.get(project.id, []),
        )
        recorded = checked.get(project.id, set())
        result[project.id] = StreakPair(
            current=current_streak(days, recorded, current),
            longest=longest_streak(days, recorded),
        )
    return result
