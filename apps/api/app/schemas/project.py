from datetime import date
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
