from fastapi import APIRouter

from app.deps import CurrentAccount
from app.schemas.today import TodayView
from app.services.business_day import DAY_CUTOVER_HOUR, today_business_date

router = APIRouter(tags=["today"])


@router.get("/today")
async def today(_account: CurrentAccount) -> TodayView:
    return TodayView(
        business_date=today_business_date(),
        timezone="Europe/Madrid",
        cutover_hour=DAY_CUTOVER_HOUR,
    )
