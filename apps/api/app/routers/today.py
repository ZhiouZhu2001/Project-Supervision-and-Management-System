from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import CurrentAccount
from app.models.log import Log
from app.models.project import Project
from app.schemas.today import Flame, LoggedEntry, TodayProject, TodayView
from app.services.business_day import DAY_CUTOVER_HOUR, today_business_date
from app.services.schedule import load_rules
from app.services.status import load_status_rules
from app.services.streak import FLAME_THRESHOLD
from app.services.streak_inputs import expected_days_for, streaks_for

router = APIRouter(tags=["today"])


@router.get("/today")
async def today(
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> TodayView:
    current = today_business_date()

    projects = list(
        await db.scalars(
            select(Project)
            .where(Project.deleted_at.is_(None), Project.status == "active")
            .order_by(Project.sort_order, Project.created_at)
        )
    )

    streaks = await streaks_for(db, projects, current=current)

    rows = await db.execute(
        select(Log.project_id, Log.id, Log.business_date, Log.content)
        .where(
            Log.deleted_at.is_(None),
            Log.business_date == current,
        )
        .order_by(Log.created_at)
    )
    latest: dict[UUID, LoggedEntry] = {
        project_id: LoggedEntry(id=log_id, content=content)
        for project_id, log_id, _business_date, content in rows
    }

    # A paused project is not on today's cards, so the is_rest_day flag only
    # ever describes projects that are expected right now.
    global_rules, by_project = await load_rules(db, until=current)
    status_rules = await load_status_rules(db, until=current)

    entries: list[TodayProject] = []
    flame: Flame | None = None

    for project in projects:
        streak = streaks[project.id].current
        days = expected_days_for(
            project,
            current=current,
            global_rules=global_rules,
            overrides=by_project.get(project.id, []),
            history=status_rules.get(project.id, []),
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
                is_rest_day=current not in days,
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
