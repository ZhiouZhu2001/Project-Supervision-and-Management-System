from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class SettingsView(BaseModel):
    """The rest-day rule in force today.

    `effective_from` is null when the account has never changed the default,
    which is a different thing from having changed it today.
    """

    rest_weekdays: list[int]
    effective_from: date | None


class RestDaysUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Seven is allowed through the schema so the service can reject it with a
    # specific code; shape validation and rule validation stay separate.
    rest_weekdays: list[int] = Field(max_length=7)
    effective_from: date | None = None
