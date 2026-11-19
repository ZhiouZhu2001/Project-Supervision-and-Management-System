from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import CurrentAccount
from app.errors import ApiError
from app.models.attachment import Attachment
from app.models.log import Log
from app.schemas.attachment import AttachmentView, attachment_url
from app.services.business_day import today_business_date
from app.services.storage import MAX_BYTES, MAX_PER_LOG, UnsupportedImage, delete_image, save_image

router = APIRouter(tags=["attachments"])


def _view(attachment: Attachment) -> AttachmentView:
    return AttachmentView(
        id=attachment.id,
        log_id=attachment.log_id,
        url=attachment_url(attachment.id),
        width=attachment.width,
        height=attachment.height,
        byte_size=attachment.bytes,
        content_type=attachment.mime,
        created_at=attachment.created_at,
    )


async def _load(db: AsyncSession, attachment_id: UUID) -> Attachment:
    attachment = await db.get(Attachment, attachment_id)
    if attachment is None or attachment.deleted_at is not None:
        raise ApiError(404, "ATTACHMENT_NOT_FOUND", "Attachment not found")
    return attachment


@router.post("/logs/{log_id}/attachments", status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    log_id: UUID,
    file: UploadFile,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> AttachmentView:
    log = await db.get(Log, log_id)
    if log is None or log.deleted_at is not None:
        raise ApiError(404, "LOG_NOT_FOUND", "Log not found")

    existing = (
        await db.scalar(
            select(func.count())
            .select_from(Attachment)
            .where(Attachment.log_id == log_id, Attachment.deleted_at.is_(None))
        )
    ) or 0
    if existing >= MAX_PER_LOG:
        raise ApiError(422, "ATTACHMENT_LIMIT_REACHED", f"At most {MAX_PER_LOG} images per log")

    # Read one byte past the limit: that is enough to reject without trusting
    # a Content-Length header the client controls.
    data = await file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ApiError(422, "ATTACHMENT_TOO_LARGE", "An image must be 5 MB or smaller")

    try:
        stored = save_image(data, today=today_business_date())
    except UnsupportedImage as exc:
        raise ApiError(
            422, "ATTACHMENT_TYPE_UNSUPPORTED", "Only JPEG, PNG and WebP are accepted"
        ) from exc

    attachment = Attachment(
        log_id=log_id,
        storage_key=stored.storage_key,
        mime=stored.mime,
        bytes=stored.bytes,
        width=stored.width,
        height=stored.height,
        sha256=stored.sha256,
    )
    db.add(attachment)
    await db.commit()
    await db.refresh(attachment)

    return _view(attachment)


@router.get("/attachments/{attachment_id}")
async def serve_attachment(
    attachment_id: UUID,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    """Session-guarded file serving.

    The body is handed to nginx through X-Accel-Redirect, so the file never
    passes through Python and the URL stays private to the session: there is
    no public path that maps to the upload directory.
    """
    attachment = await _load(db, attachment_id)

    # R: a deleted log takes its images out of reach, but keeps the rows so a
    # restore within thirty days brings the picture back with it.
    log = await db.get(Log, attachment.log_id)
    if log is None or log.deleted_at is not None:
        raise ApiError(404, "ATTACHMENT_NOT_FOUND", "Attachment not found")

    return Response(
        status_code=status.HTTP_200_OK,
        headers={
            "X-Accel-Redirect": f"/protected/{attachment.storage_key}",
            "Content-Type": attachment.mime,
            "Cache-Control": "private, max-age=300",
        },
    )


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_attachment(
    attachment_id: UUID,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    attachment = await _load(db, attachment_id)

    # Hard delete, unlike logs and projects: an image is not a record of
    # anything, so "removed" means the row and the bytes are gone, not hidden.
    await db.delete(attachment)
    await db.commit()

    delete_image(attachment.storage_key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
