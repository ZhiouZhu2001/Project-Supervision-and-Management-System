from datetime import timedelta
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.log import Log
from app.models.project import Project
from app.models.schedule import ScheduleRule
from app.models.status import ProjectStatusChange
from app.services.business_day import today_business_date
from app.services.streak_inputs import streaks_for
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

async def test_the_longest_streak_outlives_any_lookback_window(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """R6: the best ever run "never decreases", so it cannot be computed from a
    bounded lookback. A six-day run from 500 days ago is still the record."""
    await _login(client)
    project_id = await _project(client, "Long haul")
    today = today_business_date()
    started = today - timedelta(days=500)

    async with session_factory() as session:
        session.add(ScheduleRule(project_id=None, rest_weekdays=[], effective_from=started))
        project = await session.get(Project, UUID(project_id))
        assert project is not None
        project.start_date = started
        project.created_business_date = started
        for offset in range(6):
            session.add(
                Log(
                    project_id=UUID(project_id),
                    business_date=started + timedelta(days=offset),
                    content="done",
                    backfilled=False,
                )
            )
        await session.commit()

    body = (await client.get(f"{PROJECTS}/{project_id}/stats")).json()

    assert body["longest_streak"] == 6

async def test_a_finished_project_keeps_the_streak_it_had(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """R10: "the streak is frozen permanently", so tomorrow must not recompute it.

    Finishing is dated tomorrow so the finish day still counts as expected;
    today is therefore unrecorded and would become a miss, resetting the number
    to zero the day after finishing. A frozen streak reads the state at the
    finish day instead.
    """
    await _login(client)
    project_id = await _project(client, "Finished but proud")
    today = today_business_date()
    started = today - timedelta(days=6)

    async with session_factory() as session:
        session.add(ScheduleRule(project_id=None, rest_weekdays=[], effective_from=started))
        project = await session.get(Project, UUID(project_id))
        assert project is not None
        project.start_date = started
        project.created_business_date = started
        for offset in range(1, 5):
            session.add(
                Log(
                    project_id=UUID(project_id),
                    business_date=today - timedelta(days=offset),
                    content="done",
                    backfilled=False,
                )
            )
        await session.commit()

    await client.patch(f"{PROJECTS}/{project_id}/status", json={"status": "finished"})

    # Today, the endpoint still agrees with the four recorded days.
    assert (await client.get(f"{PROJECTS}/{project_id}/stats")).json()["current_streak"] == 4

    async with session_factory() as session:
        project = await session.get(Project, UUID(project_id))
        assert project is not None
        frozen = await streaks_for(session, [project], current=today + timedelta(days=2))

    assert frozen[UUID(project_id)].current == 4

async def test_rates_cover_the_whole_life_not_the_rollup_window(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """R13 counts over the range the caller means, and the default is the whole
    project. Silently switching the denominator per project (12 weeks when the
    project has any expected days there, lifetime otherwise) made the same
    number mean two different things.
    """
    await _login(client)
    project_id = (await client.post(PROJECTS, json={"name": "Long haul"})).json()["id"]
    today = today_business_date()
    started = today - timedelta(days=100)

    async with session_factory() as session:
        session.add(ScheduleRule(project_id=None, rest_weekdays=[], effective_from=started))
        project = await session.get(Project, UUID(project_id))
        assert project is not None
        project.start_date = started
        project.created_business_date = started
        await session.commit()

    body = (await client.get(STATS)).json()

    rates = next(item for item in body["projects"] if item["id"] == project_id)
    assert rates["expected_days"] == 101
