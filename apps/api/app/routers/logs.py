from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import delete, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import now_utc
from app.cursor import InvalidCursor
from app.cursor import decode as decode_cursor
from app.cursor import encode as encode_cursor
from app.db import get_session
from app.deps import CurrentAccount
from app.errors import ApiError, project_not_found
from app.models.attachment import Attachment
from app.models.log import Log
from app.models.log_tag import LogTag
from app.models.project import Project
from app.schemas.attachment import AttachmentView, attachment_url
from app.schemas.log import LogCreate, LogPage, LogUpdate, LogView
from app.services.business_day import (
    BACKFILL_MAX_PER_DAY,
    BusinessDateError,
    today_business_date,
)
from app.services.logs import BackfillLimitReached, backfilled_count, resolve_log_day
from app.services.retention import RETENTION

router = APIRouter(prefix="/logs", tags=["logs"])


async def _tags_for(db: AsyncSession, log_ids: list[UUID]) -> dict[UUID, list[str]]:
    if not log_ids:
        return {}
    rows = await db.execute(
        select(LogTag.log_id, LogTag.tag).where(LogTag.log_id.in_(log_ids)).order_by(LogTag.tag)
    )
    grouped: dict[UUID, list[str]] = {}
    for log_id, tag in rows:
        grouped.setdefault(log_id, []).append(tag)
    return grouped


async def _attachments_for(
    db: AsyncSession, log_ids: list[UUID]
) -> dict[UUID, list[AttachmentView]]:
    if not log_ids:
        return {}
    rows = await db.scalars(
        select(Attachment)
        .where(Attachment.log_id.in_(log_ids), Attachment.deleted_at.is_(None))
        .order_by(Attachment.created_at)
    )
    grouped: dict[UUID, list[AttachmentView]] = {}
    for attachment in rows:
        grouped.setdefault(attachment.log_id, []).append(
            AttachmentView(
                id=attachment.id,
                log_id=attachment.log_id,
                url=attachment_url(attachment.id),
                width=attachment.width,
                height=attachment.height,
                byte_size=attachment.bytes,
                content_type=attachment.mime,
                created_at=attachment.created_at,
            )
        )
    return grouped


async def _view(db: AsyncSession, log: Log) -> LogView:
    view = LogView.model_validate(log)
    view.tags = (await _tags_for(db, [log.id])).get(log.id, [])
    view.attachments = (await _attachments_for(db, [log.id])).get(log.id, [])
    return view


async def _load(db: AsyncSession, log_id: UUID) -> Log:
    log = await db.get(Log, log_id)
    if log is None or log.deleted_at is not None:
        raise ApiError(404, "LOG_NOT_FOUND", "Log not found")
    return log


async def _replace_tags(db: AsyncSession, log_id: UUID, tags: list[str]) -> None:
    await db.execute(delete(LogTag).where(LogTag.log_id == log_id))
    for tag in tags:
        db.add(LogTag(log_id=log_id, tag=tag))


@router.get("")
async def list_logs(
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
    project_id: UUID | None = None,
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
    limit: int = Query(default=50, ge=1, le=200),
    cursor: str | None = None,
) -> LogPage:
    query = select(Log).where(Log.deleted_at.is_(None))
    if project_id is not None:
        query = query.where(Log.project_id == project_id)
    if date_from is not None:
        query = query.where(Log.business_date >= date_from)
    if date_to is not None:
        query = query.where(Log.business_date <= date_to)
    if cursor is not None:
        try:
            bound_day, bound_created_at, bound_id = decode_cursor(cursor)
        except InvalidCursor as exc:
            raise ApiError(422, "CURSOR_INVALID", "cursor is not valid") from exc
        # Keyset, not offset: everything strictly after the last row seen.
        query = query.where(
            tuple_(Log.business_date, Log.created_at, Log.id)
            < tuple_(bound_day, bound_created_at, bound_id)
        )

    # One extra row is fetched to learn whether another page exists without
    # counting the whole table.
    rows = list(
        await db.scalars(
            query.order_by(
                Log.business_date.desc(), Log.created_at.desc(), Log.id.desc()
            ).limit(limit + 1)
        )
    )
    has_more = len(rows) > limit
    rows = rows[:limit]

    tags = await _tags_for(db, [log.id for log in rows])
    attachments = await _attachments_for(db, [log.id for log in rows])
    views: list[LogView] = []
    for log in rows:
        view = LogView.model_validate(log)
        view.tags = tags.get(log.id, [])
        view.attachments = attachments.get(log.id, [])
        views.append(view)

    next_cursor = (
        encode_cursor(rows[-1].business_date, rows[-1].created_at, rows[-1].id)
        if has_more and rows
        else None
    )
    return LogPage(items=views, next_cursor=next_cursor)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_log(
    payload: LogCreate,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> LogView:
    project = await db.get(Project, payload.project_id)
    if project is None or project.deleted_at is not None:
        raise project_not_found()

    today = today_business_date()

    try:
        day = await resolve_log_day(
            db, project=project, requested=payload.business_date, today=today
        )
    except BusinessDateError as exc:
        raise ApiError(422, exc.code, exc.message) from exc
    except BackfillLimitReached as exc:
        raise ApiError(422, "BACKFILL_LIMIT_REACHED", exc.message) from exc

    log = Log(
        project_id=project.id,
        business_date=day.business_date,
        content=payload.content,
        duration_minutes=payload.duration_minutes,
        backfilled=day.backfilled,
    )
    db.add(log)
    await db.flush()
    await _replace_tags(db, log.id, payload.tags)
    await db.commit()
    await db.refresh(log)

    return await _view(db, log)


@router.get("/backfill-status")
async def backfill_status(
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
    project_id: UUID,
    business_date: date,
) -> dict[str, int | bool]:
    """How many backfills are left, asked before writing rather than after failing."""
    used = await backfilled_count(db, project_id, business_date)
    remaining = max(0, BACKFILL_MAX_PER_DAY - used)
    return {
        "limit": BACKFILL_MAX_PER_DAY,
        "used": used,
        "remaining": remaining,
        "allowed": remaining > 0,
    }


@router.patch("/{log_id}")
async def update_log(
    log_id: UUID,
    payload: LogUpdate,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> LogView:
    log = await _load(db, log_id)
    changes = payload.model_dump(exclude_unset=True)

    if "content" in changes:
        log.content = changes["content"]
    if "duration_minutes" in changes:
        log.duration_minutes = changes["duration_minutes"]
    if "tags" in changes:
        await _replace_tags(db, log.id, changes["tags"] or [])

    log.updated_at = now_utc()
    await db.commit()
    await db.refresh(log)

    return await _view(db, log)


def _ensure_restorable(log: Log) -> None:
    """A log can be recovered for thirty days, then it is gone."""
    if log.deleted_at is not None and log.deleted_at <= now_utc() - RETENTION:
        raise ApiError(410, "LOG_EXPIRED", "This log was deleted too long ago to restore")


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log(
    log_id: UUID,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Response:
    log = await _load(db, log_id)
    log.deleted_at = now_utc()
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{log_id}/restore")
async def restore_log(
    log_id: UUID,
    _account: CurrentAccount,
    db: Annotated[AsyncSession, Depends(get_session)],
) -> LogView:
    log = await db.get(Log, log_id)
    if log is None:
        raise ApiError(404, "LOG_NOT_FOUND", "Log not found")
    _ensure_restorable(log)

    log.deleted_at = None
    log.updated_at = now_utc()
    await db.commit()
    await db.refresh(log)

    return await _view(db, log)
