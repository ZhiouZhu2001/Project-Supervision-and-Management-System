from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import CurrentAccount
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectView
from app.services.business_day import today_business_date

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
async def list_projects(
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> list[ProjectView]:
    rows = await db.scalars(
        select(Project)
        .where(Project.deleted_at.is_(None))
        .order_by(Project.sort_order, Project.created_at)
    )
    return [ProjectView.model_validate(row) for row in rows]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectView:
    today = today_business_date()

    # The creation business day is recorded separately from the user's start
    # date so that backdating cannot create a backlog (R3): counting only ever
    # starts at whichever is later.
    highest = await db.scalar(select(func.coalesce(func.max(Project.sort_order), -1)))
    project = Project(
        name=payload.name,
        note=payload.note,
        start_date=payload.start_date or today,
        created_business_date=today,
        sort_order=(highest or -1) + 1,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ProjectView.model_validate(project)
