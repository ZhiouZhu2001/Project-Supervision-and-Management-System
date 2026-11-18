from datetime import timedelta
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.log import Log
from app.models.project import Project
from app.models.schedule import ScheduleRule
from app.models.status import ProjectStatusChange
from app.services.business_day import today_business_date
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

STATS = "/api/stats"
PROJECTS = "/api/projects"
TODAY = "/api/today"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def _project(client: httpx.AsyncClient, name: str = "Write a little") -> str:
    return (await client.post(PROJECTS, json={"name": name})).json()["id"]


async def test_a_project_with_no_expected_days_shows_a_dash(client: httpx.AsyncClient) -> None:
    await _login(client)
    await _project(client)

    body = (await client.get(STATS)).json()

    rates = body["projects"][0]
    # A brand-new project on a rest day expects nothing yet.
    if rates["expected_days"] == 0:
        assert rates["completion_rate"] is None
        assert rates["clean_completion_rate"] is None


async def test_rates_distinguish_recorded_now_from_patched_later(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client)
    today = today_business_date()

    async with session_factory() as session:
        session.add(
            ScheduleRule(
                project_id=None, rest_weekdays=[], effective_from=today - timedelta(days=20)
            )
        )
        project = await session.get(Project, UUID(project_id))
        assert project is not None
        project.start_date = today - timedelta(days=9)
        project.created_business_date = today - timedelta(days=9)
        # Ten expected days: nine recorded on the day, one backfilled, and
        # one genuine miss.
        for offset in range(0, 9):
            session.add(
                Log(
                    project_id=UUID(project_id),
                    business_date=today - timedelta(days=offset),
                    content="done",
                    backfilled=offset == 5,
                )
            )
        await session.commit()

    body = (await client.get(STATS)).json()
    rates = body["projects"][0]

    assert rates["expected_days"] == 10
    assert rates["recorded_days"] == 9
    assert rates["clean_days"] == 8
    assert rates["completion_rate"] == 0.9
    assert rates["clean_completion_rate"] == 0.8


async def test_paused_and_rest_days_leave_the_denominator(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client)
    today = today_business_date()

    async with session_factory() as session:
        session.add(
            ScheduleRule(
                project_id=None, rest_weekdays=[], effective_from=today - timedelta(days=20)
            )
        )
        project = await session.get(Project, UUID(project_id))
        assert project is not None
        project.start_date = today - timedelta(days=6)
        project.created_business_date = today - timedelta(days=6)
        # Paused for two of those days.
        session.add(
            ProjectStatusChange(
                project_id=UUID(project_id),
                status="paused",
                effective_from=today - timedelta(days=4),
            )
        )
        session.add(
            ProjectStatusChange(
                project_id=UUID(project_id),
                status="active",
                effective_from=today - timedelta(days=2),
            )
        )
        await session.commit()

    body = (await client.get(STATS)).json()
    rates = body["projects"][0]

    # Seven calendar days minus two paused ones.
    assert rates["expected_days"] == 5


async def test_the_rollup_omits_weeks_with_nothing_expected(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)
    await _project(client)

    body = (await client.get(STATS)).json()

    for bucket in body["rollup"]:
        assert bucket["expected"] > 0
    assert body["rollup_weeks"] == 12


async def test_the_recent_count_covers_thirty_business_days(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)

    await client.post("/api/logs", json={"project_id": project_id, "content": "today"})
    body = (await client.get(STATS)).json()

    assert body["recent_logs"] == 1
    assert body["recent_days"] == 30


async def test_archived_projects_are_excluded(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    await client.patch(f"{PROJECTS}/{project_id}/status", json={"status": "archived"})

    body = (await client.get(STATS)).json()

    assert body["projects"] == []


async def test_everything_arrives_in_one_response(client: httpx.AsyncClient) -> None:
    await _login(client)
    await _project(client)

    body = (await client.get(STATS)).json()

    assert set(body) == {
        "business_date",
        "projects",
        "rollup",
        "recent_logs",
        "rollup_weeks",
        "recent_days",
    }


async def test_statistics_require_a_session(client: httpx.AsyncClient) -> None:
    assert (await client.get(STATS)).status_code == 401
