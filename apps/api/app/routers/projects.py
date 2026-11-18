from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import now_utc
from app.db import get_session
from app.deps import CurrentAccount
from app.errors import ApiError, project_not_found
from app.models.project import Project
from app.models.schedule import ScheduleRule
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectView,
    ScheduleUpdate,
    ScheduleView,
)
from app.services.business_day import BusinessDateError, today_business_date, validate_business_date
from app.services.schedule import DEFAULT_REST_WEEKDAYS, validate_rest_weekdays

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


async def _latest_rule(
    db: AsyncSession, *, project_id: UUID | None, today: date
) -> ScheduleRule | None:
    condition = (
        ScheduleRule.project_id.is_(None)
        if project_id is None
        else ScheduleRule.project_id == project_id
    )
    return await db.scalar(
        select(ScheduleRule)
        .where(condition, ScheduleRule.effective_from <= today)
        .order_by(ScheduleRule.effective_from.desc())
        .limit(1)
    )


async def _schedule_view(db: AsyncSession, project_id: UUID, today: date) -> ScheduleView:
    own = await _latest_rule(db, project_id=project_id, today=today)
    if own is not None:
        return ScheduleView(
            rest_weekdays=sorted(own.rest_weekdays),
            effective_from=own.effective_from,
            inherited=False,
        )

    shared = await _latest_rule(db, project_id=None, today=today)
    if shared is None:
        return ScheduleView(
            rest_weekdays=sorted(DEFAULT_REST_WEEKDAYS), effective_from=None, inherited=True
        )
    return ScheduleView(
        rest_weekdays=sorted(shared.rest_weekdays),
        effective_from=shared.effective_from,
        inherited=True,
    )


@router.get("/{project_id}/schedule")
async def read_schedule(
    project_id: UUID,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ScheduleView:
    await _load(db, project_id)
    return await _schedule_view(db, project_id, today_business_date())


@router.put("/{project_id}/schedule")
async def update_schedule(
    project_id: UUID,
    payload: ScheduleUpdate,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ScheduleView:
    await _load(db, project_id)
    today = today_business_date()

    try:
        weekdays = validate_rest_weekdays(payload.rest_weekdays)
    except ValueError as exc:
        raise ApiError(422, "REST_DAYS_INVALID", str(exc)) from exc

    effective_from = payload.effective_from or today
    try:
        validate_business_date(effective_from, today=today)
    except BusinessDateError as exc:
        raise ApiError(422, exc.code, exc.message) from exc

    # Same shape as the global rule: one row per effective date, updated in
    # place when the owner changes their mind on the same day.
    rule = await db.scalar(
        select(ScheduleRule).where(
            ScheduleRule.project_id == project_id,
            ScheduleRule.effective_from == effective_from,
        )
    )
    if rule is None:
        rule = ScheduleRule(
            project_id=project_id,
            rest_weekdays=sorted(weekdays),
            effective_from=effective_from,
        )
        db.add(rule)
    else:
        rule.rest_weekdays = sorted(weekdays)

    await db.commit()
    return await _schedule_view(db, project_id, today)


@router.delete("/{project_id}/schedule")
async def clear_schedule(
    project_id: UUID,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ScheduleView:
    """Drop the override so the project follows the account default again."""
    await _load(db, project_id)
    await db.execute(delete(ScheduleRule).where(ScheduleRule.project_id == project_id))
    await db.commit()
    return await _schedule_view(db, project_id, today_business_date())
