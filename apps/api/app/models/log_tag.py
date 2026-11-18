from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LogTag(Base):
    """A free-form label on a log.

    Tags exist so a session can be marked without maintaining a taxonomy: they
    are created by typing them and disappear when the last log using one drops
    the tag.
    """

    __tablename__ = "log_tag"

    log_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("log.id", ondelete="CASCADE"), primary_key=True
    )
    tag: Mapped[str] = mapped_column(String(24), primary_key=True)

    __table_args__ = (CheckConstraint("length(tag) BETWEEN 1 AND 24", name="ck_log_tag_length"),)
