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
