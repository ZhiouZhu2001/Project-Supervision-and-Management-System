from datetime import date

from pydantic import BaseModel


class TodayView(BaseModel):
    """What the client is allowed to know about "now".

    The business date is computed here and only here; a client that computes
    it can disagree with the server at 03:59.
    """

    business_date: date
    timezone: str
    cutover_hour: int
