from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, SmallInteger, false, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ScheduleRule(Base):
    """Which weekdays are rest days, from a date onward.

    `project_id` is null for the account-wide default; a row with a project id
    overrides it for that project alone. Rows are appended, never edited â€” the
    history of the rule is what keeps past streaks stable (R14).
    """

    __tablename__ = "schedule_rule"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE")
    )
    rest_weekdays: Mapped[list[int]] = mapped_column(ARRAY(SmallInteger), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    # True closes an override from this date onward: the project follows the
    # account default again without deleting what the old rule meant (R14).
    inherits_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (Index("ix_schedule_rule_project_effective", "project_id", "effective_from"),)

