from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.jobs.purge import purge_expired
from app.models.log import Log
from app.models.project import Project
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

PROJECTS = "/api/projects"
LOGS = "/api/logs"
TODAY = "/api/today"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def _project(client: httpx.AsyncClient, name: str = "Write a little") -> str:
    return (await client.post(PROJECTS, json={"name": name})).json()["id"]


async def _log(client: httpx.AsyncClient, project_id: str, content: str = "x") -> dict:
    return (await client.post(LOGS, json={"project_id": project_id, "content": content})).json()


async def test_deleting_a_project_hides_it_everywhere(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)

    assert (await client.delete(f"{PROJECTS}/{project_id}")).status_code == 204

    assert (await client.get(PROJECTS)).json() == []
    assert (await client.get(TODAY)).json()["projects"] == []
    assert (await client.get(f"{PROJECTS}/{project_id}")).status_code == 404


async def test_a_deleted_project_does_not_touch_its_neighbours(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)
    doomed = await _project(client, "Doomed")
    keeper = await _project(client, "Keeper")
    await _log(client, keeper, "keep this")

    await client.delete(f"{PROJECTS}/{doomed}")

    remaining = (await client.get(PROJECTS)).json()
    assert [project["name"] for project in remaining] == ["Keeper"]
    assert len((await client.get(LOGS, params={"project_id": keeper})).json()) == 1


async def test_restoring_brings_back_the_project_and_its_logs(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)
    project_id = await _project(client)
    await _log(client, project_id, "kept")
    before = (await client.get(TODAY)).json()["projects"][0]["current_streak"]
    await client.delete(f"{PROJECTS}/{project_id}")

    restored = await client.post(f"{PROJECTS}/{project_id}/restore")

    assert restored.status_code == 200
    assert restored.json()["name"] == "Write a little"
    assert len((await client.get(LOGS, params={"project_id": project_id})).json()) == 1
    assert (await client.get(TODAY)).json()["projects"][0]["current_streak"] == before


async def test_a_project_deleted_more_than_thirty_days_ago_cannot_be_restored(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client)
    await client.delete(f"{PROJECTS}/{project_id}")

    async with session_factory() as session:
        stored = await session.get(Project, UUID(project_id))
        assert stored is not None
        stored.deleted_at = datetime.now(UTC) - timedelta(days=31)
        await session.commit()

    response = await client.post(f"{PROJECTS}/{project_id}/restore")

    assert response.status_code == 410
    assert response.json()["error"]["code"] == "PROJECT_EXPIRED"


async def test_deleted_projects_can_be_listed_for_recovery(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client, "Gone but not forgotten")
    await client.delete(f"{PROJECTS}/{project_id}")

    body = (await client.get(PROJECTS, params={"include_deleted": "true"})).json()

    assert [project["name"] for project in body] == ["Gone but not forgotten"]
    assert (await client.get(PROJECTS)).json() == []


async def test_the_purge_job_removes_only_expired_rows_and_is_idempotent(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    old_id = await _project(client, "Old")
    fresh_id = await _project(client, "Fresh")
    await _log(client, old_id, "old log")
    await _log(client, fresh_id, "fresh log")

    await client.delete(f"{PROJECTS}/{old_id}")
    await client.delete(f"{PROJECTS}/{fresh_id}")

    async with session_factory() as session:
        stored = await session.get(Project, UUID(old_id))
        assert stored is not None
        stored.deleted_at = datetime.now(UTC) - timedelta(days=31)
        await session.commit()

        first = await purge_expired(session)
        second = await purge_expired(session)

        projects = await session.scalar(select(func.count()).select_from(Project))
        logs = await session.scalar(select(func.count()).select_from(Log))

    assert first.projects == 1
    assert first.logs == 1
    assert second.projects == 0
    assert second.logs == 0
    # The freshly deleted project survives; the expired one is gone entirely.
    assert projects == 1
    assert logs == 1


async def test_an_expired_log_is_purged_too(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client)
    log = await _log(client, project_id)
    await client.delete(f"{LOGS}/{log['id']}")

    async with session_factory() as session:
        stored = await session.get(Log, UUID(log["id"]))
        assert stored is not None
        stored.deleted_at = datetime.now(UTC) - timedelta(days=31)
        await session.commit()

        report = await purge_expired(session)
        remaining = await session.scalar(select(func.count()).select_from(Log))

    assert report.logs == 1
    assert remaining == 0
