from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import now_utc
from app.db import get_session
from app.deps import CurrentAccount
from app.errors import project_not_found
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectView
from app.services.business_day import today_business_date

router = APIRouter(prefix="/projects", tags=["projects"])


async def _load(db: AsyncSession, project_id: UUID) -> Project:
    project = await db.get(Project, project_id)
    if project is None or project.deleted_at is not None:
        raise project_not_found()
    return project


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
        # `highest` is 0 for the second project, and `0 or -1` is -1: an
        # explicit None check is what keeps every project's order distinct.
        sort_order=(highest if highest is not None else -1) + 1,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ProjectView.model_validate(project)


@router.get("/{project_id}")
async def get_project(
    project_id: UUID,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectView:
    return ProjectView.model_validate(await _load(db, project_id))


@router.patch("/{project_id}")
async def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectView:
    project = await _load(db, project_id)

    # exclude_unset keeps "field omitted" distinct from "field set to null",
    # so clearing a note and not touching a note are different requests.
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    project.updated_at = now_utc()

    await db.commit()
    await db.refresh(project)
    return ProjectView.model_validate(project)
