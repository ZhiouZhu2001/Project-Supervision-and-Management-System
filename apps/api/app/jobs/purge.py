"""Physically remove what was deleted more than thirty days ago.

Soft deletes exist so the owner can take something back. They are not meant
to accumulate: after the retention window a deleted row is no longer data,
it is weight. The job is safe to run repeatedly — it only touches rows that
are already past the cutoff — and it reports what it removed so a run that
did nothing is distinguishable from a run that failed.
"""

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clock import now_utc
from app.db import get_session_factory
from app.models.attachment import Attachment
from app.models.log import Log
from app.models.project import Project
from app.services.retention import RETENTION
from app.services.storage import delete_image


@dataclass
class PurgeReport:
    projects: int = 0
    logs: int = 0
    files: int = 0


async def purge_expired(db: AsyncSession, *, now: datetime | None = None) -> PurgeReport:
    cutoff = (now or now_utc()) - RETENTION

    expired_projects = list(
        await db.scalars(select(Project.id).where(Project.deleted_at <= cutoff))
    )
    expired_logs = list(await db.scalars(select(Log.id).where(Log.deleted_at <= cutoff)))
    if expired_projects:
        expired_logs += list(
            await db.scalars(select(Log.id).where(Log.project_id.in_(expired_projects)))
        )

    # Files first: if the row disappears before the file, the bytes are lost
    # to the database with no way to find them again.
    files = 0
    if expired_logs:
        paths = list(
            await db.scalars(
                select(Attachment.storage_path).where(Attachment.log_id.in_(expired_logs))
            )
        )
        for path in paths:
            delete_image(path)
            files += 1

    # Logs deleted on their own, independent of their project.
    orphan_logs = await db.execute(delete(Log).where(Log.deleted_at <= cutoff))

    project_logs = 0
    if expired_projects:
        # Explicit because the cascade would delete them anyway, but without a
        # count: the report is the only evidence the job ran.
        project_logs_result = await db.execute(
            delete(Log).where(Log.project_id.in_(expired_projects))
        )
        project_logs = project_logs_result.rowcount or 0
        await db.execute(delete(Project).where(Project.id.in_(expired_projects)))

    await db.commit()

    return PurgeReport(
        projects=len(expired_projects),
        logs=(orphan_logs.rowcount or 0) + project_logs,
        files=files,
    )


async def _main() -> None:
    async with get_session_factory()() as session:
        report = await purge_expired(session)
    print(json.dumps(asdict(report)))


if __name__ == "__main__":
    asyncio.run(_main())
