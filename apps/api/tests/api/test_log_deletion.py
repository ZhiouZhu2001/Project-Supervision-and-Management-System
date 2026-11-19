from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.log import Log
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

LOGS = "/api/logs"
PROJECTS = "/api/projects"
TODAY = "/api/today"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def _project(client: httpx.AsyncClient) -> str:
    return (await client.post(PROJECTS, json={"name": "Write a little"})).json()["id"]


async def _log(client: httpx.AsyncClient, project_id: str, content: str = "x") -> dict:
    response = await client.post(LOGS, json={"project_id": project_id, "content": content})
    assert response.status_code == 201
    return response.json()


async def test_deleting_a_log_removes_it_from_the_list(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    log = await _log(client, project_id)

    assert (await client.delete(f"{LOGS}/{log['id']}")).status_code == 204

    assert (await client.get(LOGS, params={"project_id": project_id})).json()["items"] == []


async def test_deleting_the_only_log_unrecords_the_day(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    log = await _log(client, project_id)

    before = (await client.get(TODAY)).json()["projects"][0]
    await client.delete(f"{LOGS}/{log['id']}")
    after = (await client.get(TODAY)).json()["projects"][0]

    assert before["recorded"] is True
    assert after["recorded"] is False
    assert after["current_streak"] == 0


async def test_another_log_of_the_same_day_keeps_it_recorded(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)
    project_id = await _project(client)
    first = await _log(client, project_id, "morning")
    await _log(client, project_id, "evening")

    await client.delete(f"{LOGS}/{first['id']}")

    assert (await client.get(TODAY)).json()["projects"][0]["recorded"] is True


async def test_a_deleted_log_can_be_restored_with_its_content_and_date(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)
    project_id = await _project(client)
    log = await _log(client, project_id, "keep me")
    await client.delete(f"{LOGS}/{log['id']}")

    restored = await client.post(f"{LOGS}/{log['id']}/restore")

    assert restored.status_code == 200
    assert restored.json()["content"] == "keep me"
    assert restored.json()["business_date"] == log["business_date"]
    assert len((await client.get(LOGS, params={"project_id": project_id})).json()["items"]) == 1


async def test_a_log_deleted_more_than_thirty_days_ago_cannot_be_restored(
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

    response = await client.post(f"{LOGS}/{log['id']}/restore")

    assert response.status_code == 410
    assert response.json()["error"]["code"] == "LOG_EXPIRED"


async def test_deleting_an_unknown_log_is_a_404(client: httpx.AsyncClient) -> None:
    await _login(client)

    response = await client.delete(f"{LOGS}/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


async def test_restoring_an_unknown_log_is_a_404(client: httpx.AsyncClient) -> None:
    await _login(client)

    response = await client.post(f"{LOGS}/00000000-0000-0000-0000-000000000000/restore")

    assert response.status_code == 404


async def test_deleting_twice_is_a_404(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    log = await _log(client, project_id)
    await client.delete(f"{LOGS}/{log['id']}")

    assert (await client.delete(f"{LOGS}/{log['id']}")).status_code == 404
