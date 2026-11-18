from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.attachment import AttachmentView


def _clean_tags(tags: list[str]) -> list[str]:
    seen: list[str] = []
    for tag in tags:
        value = tag.strip()
        if not value:
            continue
        if len(value) > 24:
            raise ValueError("a tag is at most 24 characters")
        if value not in seen:
            seen.append(value)
    return seen


class LogCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: UUID
    business_date: date | None = None
    content: str = Field(min_length=1, max_length=2000)
    duration_minutes: int | None = Field(default=None, ge=0, le=1440)
    tags: list[str] = Field(default_factory=list, max_length=8)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("content must not be blank")
        return stripped

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, value: list[str]) -> list[str]:
        return _clean_tags(value)


class LogUpdate(BaseModel):
    """Editable fields only.

    `business_date` and `project_id` are absent on purpose: moving a log is
    delete-plus-backfill, which keeps the seven-day window and the per-day cap
    unbypassable.
    """

    model_config = ConfigDict(extra="forbid")

    content: str | None = Field(default=None, min_length=1, max_length=2000)
    duration_minutes: int | None = Field(default=None, ge=0, le=1440)
    tags: list[str] | None = Field(default=None, max_length=8)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("content must not be blank")
        return stripped

    @field_validator("tags")
    @classmethod
    def clean_tags(cls, value: list[str] | None) -> list[str] | None:
        return None if value is None else _clean_tags(value)


class LogView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    business_date: date
    content: str
    duration_minutes: int | None
    backfilled: bool
    created_at: datetime
    tags: list[str] = Field(default_factory=list)
    attachments: list[AttachmentView] = Field(default_factory=list)
