from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AttachmentView(BaseModel):
    id: UUID
    log_id: UUID
    # The URL the client puts in an <img src>. It is session-guarded, so it
    # cannot be shared by copying it out of the page.
    url: str
    width: int
    height: int
    byte_size: int
    content_type: str
    created_at: datetime


def attachment_url(attachment_id: UUID) -> str:
    return f"/api/attachments/{attachment_id}"
