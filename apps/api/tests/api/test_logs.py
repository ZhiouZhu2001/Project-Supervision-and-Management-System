from datetime import timedelta
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.project import Project
from app.services.business_day import today_business_date
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

LOGS = "/api/logs"
PROJECTS = "/api/projects"
TODAY = "/api/today"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def _project(client: httpx.AsyncClient, name: str = "Write a little") -> str:
    response = await client.post(PROJECTS, json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


async def test_logging_requires_a_session(client: httpx.AsyncClient) -> None:
    payload = {"project_id": "00000000-0000-0000-0000-000000000000", "content": "x"}

    assert (await client.post(LOGS, json=payload)).status_code == 401


async def test_a_log_for_today_is_accepted_and_is_not_a_backfill(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)
    project_id = await _project(client)

    response = await client.post(LOGS, json={"project_id": project_id, "content": "Two hours"})

    assert response.status_code == 201
    body = response.json()
    assert body["business_date"] == today_business_date().isoformat()
    assert body["backfilled"] is False
    assert body["content"] == "Two hours"


async def test_the_content_is_stripped_and_blank_content_is_rejected(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)
    project_id = await _project(client)

    stripped = await client.post(LOGS, json={"project_id": project_id, "content": "  padded  "})
    blank = await client.post(LOGS, json={"project_id": project_id, "content": "   "})

    assert stripped.json()["content"] == "padded"
    assert blank.status_code == 422
    assert blank.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_a_duration_outside_a_day_is_rejected(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)

    response = await client.post(
        LOGS, json={"project_id": project_id, "content": "x", "duration_minutes": 1441}
    )

    assert response.status_code == 422


async def test_a_future_business_date_is_rejected(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    tomorrow = (today_business_date() + timedelta(days=1)).isoformat()

    response = await client.post(
        LOGS, json={"project_id": project_id, "content": "x", "business_date": tomorrow}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "BUSINESS_DATE_IN_FUTURE"


async def test_a_date_before_the_project_started_counting_is_rejected(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)
    # Created today, so counting starts today even though the start date is old.
    response = await client.post(PROJECTS, json={"name": "Backdated", "start_date": "2026-01-01"})
    project_id = response.json()["id"]
    yesterday = (today_business_date() - timedelta(days=1)).isoformat()

    log = await client.post(
        LOGS, json={"project_id": project_id, "content": "x", "business_date": yesterday}
    )

    assert log.status_code == 422
    assert log.json()["error"]["code"] == "BUSINESS_DATE_BEFORE_PROJECT_START"


async def test_logging_against_an_unknown_project_is_a_404(client: httpx.AsyncClient) -> None:
    await _login(client)

    response = await client.post(
        LOGS,
        json={"project_id": "00000000-0000-0000-0000-000000000000", "content": "x"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROJECT_NOT_FOUND"


async def test_two_logs_on_the_same_day_are_both_kept(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)

    first = await client.post(LOGS, json={"project_id": project_id, "content": "morning"})
    second = await client.post(LOGS, json={"project_id": project_id, "content": "evening"})

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]


async def test_today_reports_the_project_as_recorded_with_its_latest_entry(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)
    project_id = await _project(client, "Move your body")

    before = (await client.get(TODAY)).json()["projects"]
    assert before[0]["recorded"] is False
    assert before[0]["last_log"] is None

    await client.post(LOGS, json={"project_id": project_id, "content": "morning"})
    await client.post(LOGS, json={"project_id": project_id, "content": "evening"})

    after = (await client.get(TODAY)).json()["projects"]
    assert after[0]["recorded"] is True
    assert after[0]["last_log"]["content"] == "evening"


async def test_today_lists_only_active_projects(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    await _project(client, "Active one")
    paused_id = await _project(client, "Paused one")

    # There is no status endpoint yet (ticket 18), so the field is set directly;
    # this test is about the filter, not about how a project gets paused.
    async with session_factory() as session:
        project = await session.get(Project, UUID(paused_id))
        assert project is not None
        project.status = "paused"
        await session.commit()

    body = (await client.get(TODAY)).json()

    assert [project["name"] for project in body["projects"]] == ["Active one"]
