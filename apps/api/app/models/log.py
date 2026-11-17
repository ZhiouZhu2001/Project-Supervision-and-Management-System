from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Log(Base):
    """One written entry for one project on one business day.

    A log *is* the check-in (ADR 0001): there is no separate record of "did I
    check in", and deleting the last log of a day un-checks that day.
    """

    __tablename__ = "log"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("project.id", ondelete="CASCADE"), nullable=False
    )

    # The business day the owner is claiming, not the instant they typed it.
    business_date: Mapped[date] = mapped_column(Date, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)

    # Decided by the server from business_date < current business day; never
    # accepted from a client (invariant 2).
    backfilled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Reserved for Phase 2 offline replay; unused until then.
    client_id: Mapped[str | None] = mapped_column(String(64), unique=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint(
            "duration_minutes IS NULL OR duration_minutes BETWEEN 0 AND 1440",
            name="ck_log_duration_range",
        ),
        CheckConstraint("length(content) BETWEEN 1 AND 2000", name="ck_log_content_length"),
        Index(
            "ix_log_project_business_date",
            "project_id",
            "business_date",
            postgresql_where=deleted_at.is_(None),
        ),
        Index("ix_log_business_date", "business_date", postgresql_where=deleted_at.is_(None)),
    )
