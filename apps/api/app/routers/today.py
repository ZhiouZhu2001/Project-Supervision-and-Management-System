from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import CurrentAccount
from app.models.log import Log
from app.models.project import Project
from app.schemas.today import LoggedEntry, TodayProject, TodayView
from app.services.business_day import DAY_CUTOVER_HOUR, today_business_date
from app.services.streak import current_streak, expected_days, window_start

router = APIRouter(tags=["today"])


@router.get("/today")
async def today(
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> TodayView:
    current = today_business_date()
    start = window_start(current)

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
    checked: dict[UUID, set] = {}
    latest: dict[UUID, LoggedEntry] = {}
    for project_id, log_id, business_date, content, _created in rows:
        checked.setdefault(project_id, set()).add(business_date)
        if business_date == current:
            latest[project_id] = LoggedEntry(id=log_id, content=content)

    return TodayView(
        business_date=current,
        timezone="Europe/Madrid",
        cutover_hour=DAY_CUTOVER_HOUR,
        projects=[
            TodayProject(
                id=project.id,
                name=project.name,
                note=project.note,
                color=project.color,
                recorded=project.id in latest,
                last_log=latest.get(project.id),
                current_streak=current_streak(
                    expected_days(max(project.counting_from, start), current),
                    checked.get(project.id, set()),
                    current,
                ),
            )
            for project in projects
        ],
    )
