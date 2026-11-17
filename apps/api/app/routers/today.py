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

    logs = list(
        await db.scalars(
            select(Log)
            .where(Log.business_date == current, Log.deleted_at.is_(None))
            .order_by(Log.created_at)
        )
    )

    # Ordered by created_at, so the last assignment is the most recent entry.
    latest: dict[UUID, Log] = {}
    for entry in logs:
        latest[entry.project_id] = entry

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
                last_log=(
                    LoggedEntry(id=latest[project.id].id, content=latest[project.id].content)
                    if project.id in latest
                    else None
                ),
            )
            for project in projects
        ],
    )
