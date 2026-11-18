from datetime import timedelta
from uuid import UUID

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.log import Log
from app.models.project import Project
from app.models.schedule import ScheduleRule
from app.models.status import ProjectStatusChange
from app.services.business_day import today_business_date
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

PROJECTS = "/api/projects"
TODAY = "/api/today"
CALENDAR = "/api/calendar"
LOGS = "/api/logs"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def _project(client: httpx.AsyncClient, name: str = "Write a little") -> str:
    return (await client.post(PROJECTS, json={"name": name})).json()["id"]


async def _backdate(
    session_factory: async_sessionmaker[AsyncSession], project_id: str, days: int
) -> None:
    start = today_business_date() - timedelta(days=days)
    async with session_factory() as session:
        project = await session.get(Project, UUID(project_id))
        assert project is not None
        project.start_date = start
        project.created_business_date = start
        status_change = await session.scalar(
            select(ProjectStatusChange).where(ProjectStatusChange.project_id == UUID(project_id))
        )
        if status_change is not None:
            status_change.effective_from = start
        await session.commit()


async def _status(client: httpx.AsyncClient, project_id: str, status: str) -> httpx.Response:
    return await client.patch(f"{PROJECTS}/{project_id}/status", json={"status": status})


async def test_pausing_takes_effect_on_the_same_business_day(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)

    assert (await _status(client, project_id, "paused")).status_code == 200

    assert (await client.get(TODAY)).json()["projects"] == []


async def test_a_paused_day_is_not_expected_in_the_calendar(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    today = today_business_date().isoformat()
    before = {day["business_date"]: day for day in (await client.get(CALENDAR)).json()["days"]}
    await _status(client, project_id, "paused")
    after = {day["business_date"]: day for day in (await client.get(CALENDAR)).json()["days"]}

    assert before[today]["expected_count"] == 1
    assert after[today]["expected_count"] == 0
    assert after[today]["state"] == "rest"


async def test_each_status_change_is_appended_with_its_date(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client)
    await _status(client, project_id, "paused")

    async with session_factory() as session:
        rows = list(
            await session.scalars(
                select(ProjectStatusChange)
                .where(ProjectStatusChange.project_id == UUID(project_id))
                .order_by(ProjectStatusChange.effective_from)
            )
        )

    assert [row.status for row in rows] == ["active", "paused"]
    assert rows[0].effective_from == today_business_date()
    assert rows[1].effective_from == today_business_date()


async def test_resuming_makes_the_day_expected_again(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    await _status(client, project_id, "paused")
    await _status(client, project_id, "active")

    assert len((await client.get(TODAY)).json()["projects"]) == 1


async def test_the_streak_is_frozen_across_a_pause(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client)
    await _backdate(session_factory, project_id, 10)

    today = today_business_date()
    async with session_factory() as session:
        # No rest days, so "three good days" is not silently interrupted by a
        # weekend that depends on when the suite happens to run.
        session.add(
            ScheduleRule(
                project_id=None,
                rest_weekdays=[],
                effective_from=today - timedelta(days=10),
            )
        )
        # Three good days, then a pause yesterday, then a resume today. Days
        # written while they were still the day are what a streak is made of.
        for offset in (4, 3, 2):
            session.add(
                Log(
                    project_id=UUID(project_id),
                    business_date=today - timedelta(days=offset),
                    content=f"day {offset}",
                    backfilled=False,
                )
            )
        session.add_all(
            [
                ProjectStatusChange(
                    project_id=UUID(project_id),
                    status="paused",
                    effective_from=today - timedelta(days=1),
                ),
                ProjectStatusChange(
                    project_id=UUID(project_id), status="active", effective_from=today
                ),
            ]
        )
        project = await session.get(Project, UUID(project_id))
        assert project is not None
        project.status = "active"
        await session.commit()

    body = (await client.get(TODAY)).json()["projects"][0]

    # Three before the pause, three after: the paused day neither counted nor
    # broke the chain (R14), so resuming continues instead of restarting.
    assert body["current_streak"] == 3


async def test_an_impossible_transition_is_refused(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    await _status(client, project_id, "finished")

    response = await _status(client, project_id, "active")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "STATUS_TRANSITION_INVALID"


async def test_status_requires_a_valid_value(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)

    response = await client.patch(f"{PROJECTS}/{project_id}/status", json={"status": "sleeping"})

    assert response.status_code == 422


async def test_status_history_is_not_overwritten(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client)
    await _status(client, project_id, "paused")
    await _status(client, project_id, "active")

    async with session_factory() as session:
        count = await session.scalar(
            select(func.count())
            .select_from(ProjectStatusChange)
            .where(ProjectStatusChange.project_id == UUID(project_id))
        )

    assert count == 3


async def test_finishing_removes_the_project_from_today(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)

    assert len((await client.get(TODAY)).json()["projects"]) == 1
    assert (await _status(client, project_id, "finished")).status_code == 200

    assert (await client.get(TODAY)).json()["projects"] == []
    listed = (await client.get(PROJECTS)).json()
    assert [project["status"] for project in listed] == ["finished"]


async def test_a_finished_project_keeps_its_numbers(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client)
    await _backdate(session_factory, project_id, 10)

    today = today_business_date()
    async with session_factory() as session:
        session.add(
            ScheduleRule(
                project_id=None, rest_weekdays=[], effective_from=today - timedelta(days=10)
            )
        )
        for offset in (2, 1, 0):
            session.add(
                Log(
                    project_id=UUID(project_id),
                    business_date=today - timedelta(days=offset),
                    content=f"day {offset}",
                    backfilled=False,
                )
            )
        await session.commit()

    before = (await client.get(f"{PROJECTS}/{project_id}/stats")).json()
    await _status(client, project_id, "finished")
    after = (await client.get(f"{PROJECTS}/{project_id}/stats")).json()

    assert before == {"current_streak": 3, "longest_streak": 3}
    assert after == before


async def test_a_finished_project_cannot_be_unfinished(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    await _status(client, project_id, "finished")

    for target in ("active", "paused"):
        response = await _status(client, project_id, target)
        assert response.status_code == 422, target

    assert (await _status(client, project_id, "archived")).status_code == 200
