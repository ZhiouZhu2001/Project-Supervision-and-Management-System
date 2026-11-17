from datetime import timedelta
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.log import Log
from app.models.project import Project
from app.services.business_day import today_business_date
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

TODAY = "/api/today"
PROJECTS = "/api/projects"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def _project(client: httpx.AsyncClient, name: str = "Write a little") -> UUID:
    response = await client.post(PROJECTS, json={"name": name})
    assert response.status_code == 201
    return UUID(response.json()["id"])


async def _backdate_and_log(
    session_factory: async_sessionmaker[AsyncSession],
    project_id: UUID,
    offsets: list[int],
) -> None:
    """Give the project a past counting start and logs on the given day offsets.

    The API refuses to create history before a project existed (R3), so a
    multi-day streak can only be set up by writing the rows a real history
    would have produced.
    """
    today = today_business_date()
    start = today - timedelta(days=max(offsets))
    async with session_factory() as session:
        project = await session.get(Project, project_id)
        assert project is not None
        project.start_date = start
        project.created_business_date = start
        for offset in offsets:
            session.add(
                Log(
                    project_id=project_id,
                    business_date=today - timedelta(days=offset),
                    content=f"day -{offset}",
                )
            )
        await session.commit()


async def test_today_requires_a_session(client: httpx.AsyncClient) -> None:
    assert (await client.get(TODAY)).status_code == 401


async def test_today_returns_the_server_side_business_date(client: httpx.AsyncClient) -> None:
    await _login(client)

    response = await client.get(TODAY)

    assert response.status_code == 200
    body = response.json()
    assert body["business_date"] == today_business_date().isoformat()
    assert body["timezone"] == "Europe/Madrid"
    assert body["cutover_hour"] == 4


async def test_a_brand_new_project_has_no_streak(client: httpx.AsyncClient) -> None:
    await _login(client)
    await _project(client)

    body = (await client.get(TODAY)).json()

    assert body["projects"][0]["current_streak"] == 0


async def test_recording_today_gives_a_streak_of_one(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)

    await client.post("/api/logs", json={"project_id": str(project_id), "content": "x"})
    body = (await client.get(TODAY)).json()

    assert body["projects"][0]["current_streak"] == 1


async def test_four_consecutive_days_is_a_streak_of_four(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client)
    await _backdate_and_log(session_factory, project_id, [3, 2, 1, 0])

    body = (await client.get(TODAY)).json()

    assert body["projects"][0]["current_streak"] == 4


async def test_a_missing_day_breaks_the_chain(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client)
    # Yesterday is missing, so only today counts.
    await _backdate_and_log(session_factory, project_id, [4, 3, 2, 0])

    body = (await client.get(TODAY)).json()

    assert body["projects"][0]["current_streak"] == 1


async def test_an_unrecorded_today_counts_yesterdays_run(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client)
    await _backdate_and_log(session_factory, project_id, [3, 2, 1])

    body = (await client.get(TODAY)).json()

    assert body["projects"][0]["recorded"] is False
    assert body["projects"][0]["current_streak"] == 3
