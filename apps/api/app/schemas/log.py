from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LogCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: UUID
    business_date: date | None = None
    content: str = Field(min_length=1, max_length=2000)
    duration_minutes: int | None = Field(default=None, ge=0, le=1440)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("content must not be blank")
        return stripped


class LogView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    business_date: date
    content: str
    duration_minutes: int | None
    backfilled: bool
    created_at: datetime
