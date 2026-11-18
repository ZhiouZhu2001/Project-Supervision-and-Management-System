from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Attachment(Base):
    """An image on a log.

    `storage_path` is relative to the upload root and is built from a random
    name: the owner's filename never reaches the disk, the URL or the logs
    (security section of AGENTS.md).
    """

    __tablename__ = "attachment"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    log_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("log.id", ondelete="CASCADE"), nullable=False
    )
    storage_path: Mapped[str] = mapped_column(String(160), nullable=False)
    content_type: Mapped[str] = mapped_column(String(40), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    # Digest of the stored bytes, so an export can prove a file is the same one
    # without carrying the file itself.
    sha256: Mapped[str | None] = mapped_column(String(64))
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
