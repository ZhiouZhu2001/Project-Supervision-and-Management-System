from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    start_date: date | None = None
    note: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be blank")
        return stripped


class ProjectUpdate(BaseModel):
    """Only the fields a project owner can change in place.

    `extra="forbid"` is what makes "changing the start date is a different
    operation" a 422 rather than a silent no-op: a client that sends
    `start_date` or `status` is told it is wrong.
    """

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=60)
    note: str | None = Field(default=None, max_length=2000)
    color: str | None = Field(default=None, max_length=16)
    emoji: str | None = Field(default=None, max_length=8)
    sort_order: int | None = Field(default=None, ge=0)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be blank")
        return stripped


class ProjectView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    note: str | None
    color: str | None
    emoji: str | None
    start_date: date
    created_business_date: date
    status: str
    sort_order: int
    # Non-null only when the caller asked for deleted projects, which is what
    # makes the recovery list possible without a second endpoint.
    deleted_at: datetime | None = None


class ScheduleView(BaseModel):
    """The rest-day rule in force for one project today (R7)."""

    rest_weekdays: list[int]
    effective_from: date | None
    inherited: bool


class ScheduleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rest_weekdays: list[int] = Field(max_length=7)
    effective_from: date | None = None


class StatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["active", "paused", "finished", "archived"]
