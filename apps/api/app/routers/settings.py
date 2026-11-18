from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import CurrentAccount
from app.errors import ApiError
from app.models.schedule import ScheduleRule
from app.schemas.settings import RestDaysUpdate, SettingsView
from app.services.business_day import BusinessDateError, today_business_date, validate_business_date
from app.services.schedule import DEFAULT_REST_WEEKDAYS, validate_rest_weekdays

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
async def read_settings(
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> SettingsView:
    today = today_business_date()
    rule = await db.scalar(
        select(ScheduleRule)
        .where(ScheduleRule.project_id.is_(None), ScheduleRule.effective_from <= today)
        .order_by(ScheduleRule.effective_from.desc())
        .limit(1)
    )

    if rule is None:
        return SettingsView(rest_weekdays=sorted(DEFAULT_REST_WEEKDAYS), effective_from=None)
    return SettingsView(
        rest_weekdays=sorted(rule.rest_weekdays), effective_from=rule.effective_from
    )


@router.put("/rest-days")
async def update_rest_days(
    payload: RestDaysUpdate,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> SettingsView:
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

    # One rule per (project, effective date). Changing the setting twice on
    # the same day updates today's rule rather than colliding with the unique
    # index: no earlier rule exists for today, so nothing historical moves.
    rule = await db.scalar(
        select(ScheduleRule).where(
            ScheduleRule.project_id.is_(None),
            ScheduleRule.effective_from == effective_from,
        )
    )
    if rule is None:
        rule = ScheduleRule(
            project_id=None,
            rest_weekdays=sorted(weekdays),
            effective_from=effective_from,
        )
        db.add(rule)
    else:
        rule.rest_weekdays = sorted(weekdays)

    await db.commit()
    await db.refresh(rule)

    return SettingsView(
        rest_weekdays=sorted(rule.rest_weekdays), effective_from=rule.effective_from
    )
