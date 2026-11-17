from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import CurrentAccount
from app.errors import ApiError, project_not_found
from app.models.log import Log
from app.models.project import Project
from app.schemas.log import LogCreate, LogView
from app.services.business_day import BusinessDateError, today_business_date, validate_business_date

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_log(
    payload: LogCreate,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> LogView:
    project = await db.get(Project, payload.project_id)
    if project is None or project.deleted_at is not None:
        raise project_not_found()

    today = today_business_date()
    business_date = payload.business_date or today

    try:
        validate_business_date(business_date, today=today)
    except BusinessDateError as exc:
        raise ApiError(422, exc.code, exc.message) from exc

    # R3: counting starts at whichever is later, so a log before that would be
    # a record of a day the project did not yet exist.
    if business_date < project.counting_from:
        raise ApiError(
            422,
            "BUSINESS_DATE_BEFORE_PROJECT_START",
            "A log cannot predate the day the project started counting",
        )

    log = Log(
        project_id=project.id,
        business_date=business_date,
        content=payload.content,
        duration_minutes=payload.duration_minutes,
        # R9: derived, never supplied by the client.
        backfilled=business_date < today,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    return LogView.model_validate(log)
