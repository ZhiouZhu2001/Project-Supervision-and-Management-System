from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

STATUSES = ("active", "paused", "finished", "archived")


class ProjectStatusChange(Base):
    """One row per status, with the day it took effect.

    Status is history, not a field: a pause last month must not rewrite the
    days before it (R14). `project.status` stays as the denormalised current
    value so lists do not need a correlated subquery.
    """

    __tablename__ = "project_status_change"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        # Not unique: a pause and a resume on the same day are two real acts.
        # `status_on` resolves by (effective_from, created_at), so the latest
        # row wins while the earlier one stays on the record.
        Index(
            "ix_project_status_change_project_effective",
            "project_id",
            "effective_from",
        ),
    )
