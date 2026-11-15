from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Account(Base):
    """The single user of the system.

    Exactly one row exists. It is seeded from configuration on first boot;
    there is no registration path anywhere in the application.
    """

    __tablename__ = "account"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(80))
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Madrid")
    day_cutover_hour: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=4)
    alert_hour: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=21)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
