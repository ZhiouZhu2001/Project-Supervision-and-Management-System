import calendar as month_calendar
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import CurrentAccount
from app.errors import ApiError
from app.models.log import Log
from app.models.project import Project
from app.models.schedule import ScheduleRule
from app.schemas.calendar import CalendarDay, CalendarView
from app.services.business_day import backfill_window, today_business_date
from app.services.schedule import DEFAULT_REST_WEEKDAYS, RestRule, rest_weekdays_for
from app.services.status import load_status_rules, status_on

router = APIRouter(tags=["calendar"])


def _month_bounds(month: str) -> tuple[date, date]:
    try:
        year_text, month_text = month.split("-")
        year, month_number = int(year_text), int(month_text)
        last = month_calendar.monthrange(year, month_number)[1]
    except (ValueError, IndexError) as exc:
        raise ApiError(422, "MONTH_INVALID", "month must look like YYYY-MM") from exc

    return date(year, month_number, 1), date(year, month_number, last)


def _state(expected: int, done: int, *, is_future: bool) -> str:
    if is_future:
        return "future"
    if expected == 0:
        # Rest days, days before a project started, paused spans: nothing was
        # required, so the day is not a failure.
        return "rest"
    if done == 0:
        return "none"
    ratio = done / expected
    if ratio >= 1:
        return "all"
    if ratio >= 0.5:
        return "most"
    return "partial"


@router.get("/calendar")
async def read_calendar(
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
    month: str | None = Query(
        default=None, description="YYYY-MM; defaults to the current business month"
    ),
) -> CalendarView:
    today = today_business_date()
    month = month or today.strftime("%Y-%m")

    start, end = _month_bounds(month)
    window_start, _window_end = backfill_window(today)

    rules = list(
        await db.scalars(
            select(ScheduleRule)
            .where(ScheduleRule.effective_from <= end)
            .order_by(ScheduleRule.effective_from)
        )
    )
    global_rules: list[RestRule] = []
    by_project: dict[UUID, list[RestRule]] = {}
    for rule in rules:
        entry: RestRule = (rule.effective_from, frozenset(rule.rest_weekdays))
        if rule.project_id is None:
            global_rules.append(entry)
        else:
            by_project.setdefault(rule.project_id, []).append(entry)

    projects = list(
        await db.scalars(
            select(Project)
            .where(
                Project.deleted_at.is_(None),
                Project.created_business_date <= end,
                Project.start_date <= end,
            )
            .order_by(Project.sort_order, Project.created_at)
        )
    )

    rows = await db.execute(
        select(Log.project_id, Log.business_date)
        .where(Log.deleted_at.is_(None), Log.business_date >= start, Log.business_date <= end)
        .distinct()
    )
    logged: set[tuple[UUID, date]] = {(project_id, day) for project_id, day in rows}
    status_rules = await load_status_rules(db, until=end)

    backfilled_rows = await db.execute(
        select(Log.business_date, func.count())
        .where(
            Log.deleted_at.is_(None),
            Log.backfilled.is_(True),
            Log.business_date >= start,
            Log.business_date <= end,
        )
        .group_by(Log.business_date)
    )
    backfilled_counts: dict[date, int] = {day: count for day, count in backfilled_rows}

    days: list[CalendarDay] = []
    cursor = start
    while cursor <= end:
        expected = 0
        done = 0
        for project in projects:
            if cursor < project.counting_from:
                continue
            # R14: a paused project expected nothing on that day.
            if status_on(cursor, status_rules.get(project.id, [])) != "active":
                continue

            overrides = by_project.get(project.id, [])
            base = rest_weekdays_for(cursor, global_rules, DEFAULT_REST_WEEKDAYS)
            if cursor.isoweekday() in rest_weekdays_for(cursor, overrides, base):
                continue

            expected += 1
            if (project.id, cursor) in logged:
                done += 1

        days.append(
            CalendarDay(
                business_date=cursor,
                expected_count=expected,
                done_count=done,
                state=_state(expected, done, is_future=cursor > today),
                backfilled_count=backfilled_counts.get(cursor, 0),
                can_backfill=window_start <= cursor <= today,
            )
        )
        cursor = date.fromordinal(cursor.toordinal() + 1)

    return CalendarView(
        month=month,
        today=today,
        first_weekday=start.isoweekday(),
        days=days,
    )
