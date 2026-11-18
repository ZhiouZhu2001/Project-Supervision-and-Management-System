from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import CurrentAccount
from app.models.log import Log
from app.models.project import Project
from app.models.schedule import ScheduleRule
from app.schemas.today import Flame, LoggedEntry, TodayProject, TodayView
from app.services.business_day import DAY_CUTOVER_HOUR, today_business_date
from app.services.schedule import DEFAULT_REST_WEEKDAYS, RestRule, rest_weekdays_for
from app.services.streak import FLAME_THRESHOLD, current_streak, expected_days, window_start

router = APIRouter(tags=["today"])


async def _rules(
    db: AsyncSession, current: date
) -> tuple[list[RestRule], dict[UUID, list[RestRule]]]:
    """Split the rules in force into the account default and per-project overrides."""
    rows = list(
        await db.scalars(
            select(ScheduleRule)
            .where(ScheduleRule.effective_from <= current)
            .order_by(ScheduleRule.effective_from)
        )
    )

    global_rules: list[RestRule] = []
    by_project: dict[UUID, list[RestRule]] = {}
    for rule in rows:
        entry: RestRule = (rule.effective_from, frozenset(rule.rest_weekdays))
        if rule.project_id is None:
            global_rules.append(entry)
        else:
            by_project.setdefault(rule.project_id, []).append(entry)
    return global_rules, by_project


@router.get("/today")
async def today(
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> TodayView:
    current = today_business_date()
    start = window_start(current)
    global_rules, project_rules = await _rules(db, current)

    projects = list(
        await db.scalars(
            select(Project)
            .where(Project.deleted_at.is_(None), Project.status == "active")
            .order_by(Project.sort_order, Project.created_at)
        )
    )

    # One query for the whole window: streaks are computed in memory from
    # these sets, never with a query per project.
    rows = await db.execute(
        select(Log.project_id, Log.id, Log.business_date, Log.content, Log.created_at)
        .where(Log.deleted_at.is_(None), Log.business_date >= start, Log.business_date <= current)
        .order_by(Log.created_at)
    )
    checked: dict[UUID, set[date]] = {}
    latest: dict[UUID, LoggedEntry] = {}
    for project_id, log_id, business_date, content, _created in rows:
        checked.setdefault(project_id, set()).add(business_date)
        if business_date == current:
            latest[project_id] = LoggedEntry(id=log_id, content=content)

    entries: list[TodayProject] = []
    flame: Flame | None = None

    for project in projects:
        overrides = project_rules.get(project.id, [])

        def rest_on(day: date, overrides: list[RestRule] = overrides) -> frozenset[int]:
            # Project rules win over the account default, day by day (R7/R14).
            base = rest_weekdays_for(day, global_rules, DEFAULT_REST_WEEKDAYS)
            return rest_weekdays_for(day, overrides, base)

        streak = current_streak(
            expected_days(max(project.counting_from, start), current, rest_for=rest_on),
            checked.get(project.id, set()),
            current,
        )
        entries.append(
            TodayProject(
                id=project.id,
                name=project.name,
                note=project.note,
                color=project.color,
                recorded=project.id in latest,
                last_log=latest.get(project.id),
                current_streak=streak,
                is_rest_day=current.isoweekday() in rest_on(current),
            )
        )
        # R11: the flame belongs to the best streak, not to the sum.
        if streak >= FLAME_THRESHOLD and (flame is None or streak > flame.streak):
            flame = Flame(streak=streak, project_name=project.name)

    return TodayView(
        business_date=current,
        timezone="Europe/Madrid",
        cutover_hour=DAY_CUTOVER_HOUR,
        projects=entries,
        flame=flame,
    )
