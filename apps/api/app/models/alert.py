from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Date, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AlertLog(Base):
    """One row per business day the digest job judged.

    Invariant 6: `business_date` is unique, so running the job twice cannot
    send twice. The row is written even when nothing was sent, because a quiet
    day and a dead scheduler must not look the same.
    """

    __tablename__ = "alert_log"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    business_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    # sent | skipped | failed | pending. `skipped` means the day owed nothing;
    # `pending` means a send was started and its outcome is unknown (a crash),
    # which is deliberately not retried — a second send is the outcome
    # invariant 6 forbids.
    outcome: Mapped[str] = mapped_column(String(16), nullable=False)
    # Which projects the message named. Storing the ids keeps the digest
    # auditable after a project is renamed or deleted, which a count cannot.
    project_ids: Mapped[list[UUID]] = mapped_column(
        ARRAY(PGUUID(as_uuid=True)), nullable=False, server_default="{}"
    )
    recipient: Mapped[str | None] = mapped_column(String(255))
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Declared on the model as well as in the migration: the test database is
    # built from metadata, so a vocabulary that only exists in one place is a
    # bug that waits until the application boots against a migrated database.
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('sent','skipped','failed','pending')", name="ck_alert_log_outcome"
        ),
    )
