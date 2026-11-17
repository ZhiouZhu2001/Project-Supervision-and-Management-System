from datetime import date
from uuid import UUID

from pydantic import BaseModel


class LoggedEntry(BaseModel):
    id: UUID
    content: str


class TodayProject(BaseModel):
    id: UUID
    name: str
    note: str | None
    color: str | None
    recorded: bool
    last_log: LoggedEntry | None


class TodayView(BaseModel):
    """What the client is allowed to know about "now".

    The business date is computed here and only here; a client that computes
    it can disagree with the server at 03:59.
    """

    business_date: date
    timezone: str
    cutover_hour: int
    projects: list[TodayProject]
