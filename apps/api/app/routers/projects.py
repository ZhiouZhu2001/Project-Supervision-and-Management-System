from datetime import timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import now_utc
from app.db import get_session
from app.deps import CurrentAccount
from app.errors import ApiError, project_not_found
from app.models.project import Project
from app.models.status import ProjectStatusChange
from app.schemas.project import (
    ProjectCreate,
    ProjectListed,
    ProjectUpdate,
    ProjectView,
    ScheduleUpdate,
    ScheduleView,
    StatusUpdate,
)
from app.services.business_day import BusinessDateError, today_business_date, validate_business_date
from app.services.retention import RETENTION
from app.services.schedule import (
    ScheduleInForce,
    clear_override,
    schedule_in_force,
    set_override,
    validate_rest_weekdays,
)
from app.services.status import can_transition
from app.services.streak_inputs import streaks_for

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
    include_deleted: bool = False,
    status_filter: Annotated[
        Literal["active", "paused", "finished", "archived"] | None, Query(alias="status")
    ] = None,
) -> list[ProjectListed]:
    query = select(Project)
    if not include_deleted:
        query = query.where(Project.deleted_at.is_(None))
    if status_filter is not None:
        query = query.where(Project.status == status_filter)

    rows = list(await db.scalars(query.order_by(Project.sort_order, Project.created_at)))
    if not rows:
        return []

    # One batched computation for the whole page: a per-project query here is
    # the N+1 the streak module's docs warn about.
    streaks = await streaks_for(db, rows, current=today_business_date())
    return [
        ProjectListed(
            **ProjectView.model_validate(row).model_dump(),
            current_streak=streaks[row.id].current,
            longest_streak=streaks[row.id].longest,
        )
        for row in rows
    ]


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
    await db.flush()
    # The first status row is dated to the day counting starts, so the history
    # is complete from the beginning rather than from the first change.
    db.add(
        ProjectStatusChange(
            project_id=project.id, status="active", effective_from=project.created_business_date
        )
    )
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


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    project = await _load(db, project_id)
    project.deleted_at = now_utc()
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{project_id}/restore")
async def restore_project(
    project_id: UUID,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectView:
    project = await db.get(Project, project_id)
    if project is None:
        raise project_not_found()

    if project.deleted_at is not None and project.deleted_at <= now_utc() - RETENTION:
        raise ApiError(410, "PROJECT_EXPIRED", "This project was deleted too long ago to restore")

    project.deleted_at = None
    project.updated_at = now_utc()
    await db.commit()
    await db.refresh(project)
    return ProjectView.model_validate(project)


@router.patch("/{project_id}/status")
async def change_status(
    project_id: UUID,
    payload: StatusUpdate,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ProjectView:
    project = await _load(db, project_id)
    today = today_business_date()

    if not can_transition(project.status, payload.status):
        raise ApiError(
            422,
            "STATUS_TRANSITION_INVALID",
            f"A project cannot go from {project.status} to {payload.status}",
        )

    # R14: appended, never overwritten. A pause and a resume on the same day
    # are two rows; the newest one is the one in force.
    #
    # Finishing is also dated tomorrow, so the day it is finished on still
    # counts as an expected day: a record may never shrink because of an
    # administrative act. A pause stays dated today, because pausing says
    # "not now".
    effective_from = today + timedelta(days=1) if payload.status == "finished" else today

    db.add(
        ProjectStatusChange(
            project_id=project_id, status=payload.status, effective_from=effective_from
        )
    )

    project.status = payload.status
    project.updated_at = now_utc()
    await db.commit()
    await db.refresh(project)
    return ProjectView.model_validate(project)


@router.get("/{project_id}/stats")
async def project_stats(
    project_id: UUID,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, int]:
    """The two numbers a finished project keeps for good (R6)."""
    project = await _load(db, project_id)
    streaks = await streaks_for(db, [project], current=today_business_date())
    pair = streaks[project.id]
    return {"current_streak": pair.current, "longest_streak": pair.longest}


def _schedule_view(info: ScheduleInForce) -> ScheduleView:
    return ScheduleView(
        rest_weekdays=sorted(info.rest_weekdays),
        effective_from=info.effective_from,
        inherited=info.inherited,
    )


@router.get("/{project_id}/schedule")
async def read_schedule(
    project_id: UUID,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ScheduleView:
    await _load(db, project_id)
    info = await schedule_in_force(db, project_id=project_id, today=today_business_date())
    return _schedule_view(info)


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

    await set_override(
        db, project_id=project_id, weekdays=weekdays, effective_from=effective_from
    )
    info = await schedule_in_force(db, project_id=project_id, today=today)
    return _schedule_view(info)


@router.delete("/{project_id}/schedule")
async def clear_schedule(
    project_id: UUID,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> ScheduleView:
    """Stop the override from today, without rewriting what it meant before (R14)."""
    await _load(db, project_id)
    today = today_business_date()
    await clear_override(db, project_id=project_id, today=today)
    info = await schedule_in_force(db, project_id=project_id, today=today)
    return _schedule_view(info)