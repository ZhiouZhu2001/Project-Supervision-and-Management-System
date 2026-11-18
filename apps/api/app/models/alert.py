from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, Integer, String, Text, func
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
    # sent | no_misses | failed
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    project_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
