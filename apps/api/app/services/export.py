"""One file with everything the owner wrote (R13).

Deliberately not a backup: it carries no authentication material and no file
bytes, only the metadata that lets the owner know what exists. Its job is to
make leaving this system possible, not to restore it byte for byte.
"""

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import now_utc
from app.models.attachment import Attachment
from app.models.log import Log
from app.models.log_tag import LogTag
from app.models.project import Project
from app.models.schedule import ScheduleRule
from app.models.status import ProjectStatusChange

EXPORT_VERSION = 1


def _iso(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


async def build_export(db: AsyncSession, *, email: str) -> dict[str, Any]:
    projects = list(await db.scalars(select(Project).order_by(Project.created_at)))
    logs = list(await db.scalars(select(Log).order_by(Log.business_date, Log.created_at)))
    tags = list(await db.scalars(select(LogTag).order_by(LogTag.log_id, LogTag.tag)))
    attachments = list(await db.scalars(select(Attachment).order_by(Attachment.created_at)))
    rules = list(
        await db.scalars(
            select(ScheduleRule).order_by(ScheduleRule.effective_from, ScheduleRule.created_at)
        )
    )
    statuses = list(
        await db.scalars(
            select(ProjectStatusChange).order_by(
                ProjectStatusChange.effective_from, ProjectStatusChange.created_at
            )
        )
    )

    tags_by_log: dict[str, list[str]] = {}
    for tag in tags:
        tags_by_log.setdefault(str(tag.log_id), []).append(tag.tag)

    return {
        "export_version": EXPORT_VERSION,
        "exported_at": now_utc().isoformat(),
        # Identity only: no password hash, no session token, no secret.
        "account": {"email": email},
        "projects": [
            {
                "id": str(project.id),
                "name": project.name,
                "note": project.note,
                "color": project.color,
                "emoji": project.emoji,
                "start_date": project.start_date.isoformat(),
                "created_business_date": project.created_business_date.isoformat(),
                "status": project.status,
                "sort_order": project.sort_order,
                "created_at": _iso(project.created_at),
                "updated_at": _iso(project.updated_at),
                "deleted_at": _iso(project.deleted_at),
            }
            for project in projects
        ],
        # Soft-deleted rows are included and flagged: "everything I wrote"
        # includes what I wrote and then removed, which is still my record.
        "logs": [
            {
                "id": str(log.id),
                "project_id": str(log.project_id),
                "business_date": log.business_date.isoformat(),
                "content": log.content,
                "duration_minutes": log.duration_minutes,
                "backfilled": log.backfilled,
                "created_at": _iso(log.created_at),
                "updated_at": _iso(log.updated_at),
                "deleted_at": _iso(log.deleted_at),
                "tags": tags_by_log.get(str(log.id), []),
                "attachments": [
                    str(attachment.id) for attachment in attachments if attachment.log_id == log.id
                ],
            }
            for log in logs
        ],
        "attachments": [
            {
                "id": str(attachment.id),
                "log_id": str(attachment.log_id),
                "storage_path": attachment.storage_key,
                "content_type": attachment.mime,
                "byte_size": attachment.bytes,
                "width": attachment.width,
                "height": attachment.height,
                "sha256": attachment.sha256,
                "created_at": _iso(attachment.created_at),
                # The bytes are not part of the export; this says where they
                # live so a restore knows what to go looking for.
                "bytes_included": False,
            }
            for attachment in attachments
        ],
        "schedule_rules": [
            {
                "id": str(rule.id),
                "project_id": str(rule.project_id) if rule.project_id else None,
                "rest_weekdays": list(rule.rest_weekdays),
                "effective_from": rule.effective_from.isoformat(),
                "created_at": _iso(rule.created_at),
            }
            for rule in rules
        ],
        "project_status_changes": [
            {
                "id": str(status.id),
                "project_id": str(status.project_id),
                "status": status.status,
                "effective_from": status.effective_from.isoformat(),
                "created_at": _iso(status.created_at),
            }
            for status in statuses
        ],
    }
