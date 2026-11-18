from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import CurrentAccount
from app.schemas.stats import ProjectRatesView, StatisticsView, WeekBucketView
from app.services.business_day import today_business_date
from app.services.stats import RECENT_DAYS, ROLLUP_WEEKS, build_statistics

router = APIRouter(tags=["stats"])


@router.get("/stats")
async def read_statistics(
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> StatisticsView:
    """Everything the statistics page needs, in one round trip (ticket 24)."""
    current = today_business_date()
    statistics = await build_statistics(db, current=current)

    return StatisticsView(
        business_date=current,
        projects=[
            ProjectRatesView(
                id=rates.project.id,
                name=rates.project.name,
                status=rates.project.status,
                expected_days=rates.expected,
                recorded_days=rates.recorded,
                clean_days=rates.clean,
                completion_rate=rates.completion_rate,
                clean_completion_rate=rates.clean_completion_rate,
                current_streak=rates.current_streak,
                longest_streak=rates.longest_streak,
            )
            for rates in statistics.projects
        ],
        rollup=[
            WeekBucketView(
                week_start=bucket.week_start, expected=bucket.expected, recorded=bucket.recorded
            )
            for bucket in statistics.rollup
        ],
        recent_logs=statistics.recent_logs,
        rollup_weeks=ROLLUP_WEEKS,
        recent_days=RECENT_DAYS,
    )
