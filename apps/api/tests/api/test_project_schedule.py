from datetime import date, timedelta
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.project import Project
from app.models.schedule import ScheduleRule
from app.services.business_day import today_business_date
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

PROJECTS = "/api/projects"
STATS = "/api/stats"
TODAY = "/api/today"
LOGS = "/api/logs"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def _project(client: httpx.AsyncClient, name: str = "Write a little") -> str:
    response = await client.post(PROJECTS, json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


async def test_a_project_inherits_the_account_default(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)

    body = (await client.get(f"{PROJECTS}/{project_id}/schedule")).json()

    assert body == {"rest_weekdays": [6, 7], "effective_from": None, "inherited": True}


async def test_an_override_replaces_the_default_for_that_project_only(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)
    overridden = await _project(client, "Overridden")
    untouched = await _project(client, "Untouched")

    saved = await client.put(f"{PROJECTS}/{overridden}/schedule", json={"rest_weekdays": [1]})

    assert saved.status_code == 200
    assert saved.json()["inherited"] is False
    assert saved.json()["rest_weekdays"] == [1]
    assert (await client.get(f"{PROJECTS}/{untouched}/schedule")).json()["rest_weekdays"] == [6, 7]


async def test_an_override_changes_only_its_own_project_streak(client: httpx.AsyncClient) -> None:
    await _login(client)
    overridden = await _project(client, "Overridden")
    untouched = await _project(client, "Untouched")
    for project_id in (overridden, untouched):
        assert (
            await client.post(LOGS, json={"project_id": project_id, "content": "today"})
        ).status_code == 201

    # Make today a rest day for one project only.
    business_date = (await client.get(TODAY)).json()["business_date"]
    weekday = date.fromisoformat(business_date).isoweekday()
    await client.put(f"{PROJECTS}/{overridden}/schedule", json={"rest_weekdays": [weekday]})

    body = (await client.get(TODAY)).json()
    by_name = {project["name"]: project for project in body["projects"]}

    assert by_name["Overridden"]["is_rest_day"] is True
    assert by_name["Overridden"]["current_streak"] == 0
    assert by_name["Untouched"]["is_rest_day"] is False
    assert by_name["Untouched"]["current_streak"] == 1


async def test_clearing_an_override_returns_to_the_default(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    await client.put(f"{PROJECTS}/{project_id}/schedule", json={"rest_weekdays": [1]})

    cleared = await client.delete(f"{PROJECTS}/{project_id}/schedule")

    assert cleared.status_code == 200
    assert cleared.json()["inherited"] is True
    assert cleared.json()["rest_weekdays"] == [6, 7]


async def test_all_seven_rest_days_is_refused_for_a_project(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)

    response = await client.put(
        f"{PROJECTS}/{project_id}/schedule", json={"rest_weekdays": [1, 2, 3, 4, 5, 6, 7]}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REST_DAYS_INVALID"


async def test_an_override_can_be_changed_twice_in_one_day(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)

    await client.put(f"{PROJECTS}/{project_id}/schedule", json={"rest_weekdays": [1]})
    second = await client.put(f"{PROJECTS}/{project_id}/schedule", json={"rest_weekdays": [2]})

    assert second.status_code == 200
    assert second.json()["rest_weekdays"] == [2]


async def test_schedule_requires_a_session(client: httpx.AsyncClient) -> None:
    response = await client.get(f"{PROJECTS}/00000000-0000-0000-0000-000000000000/schedule")

    assert response.status_code == 401

async def test_clearing_an_override_does_not_touch_the_past(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """R14: closing an override appends a row; it never deletes history.

    Deleting the rules would resurrect the days the owner had exempted, which
    is exactly the retrospective rewrite R7 forbids.
    """
    await _login(client)
    response = await client.post(PROJECTS, json={"name": "Weekend-ish"})
    project_id = response.json()["id"]
    today = today_business_date()
    started = today - timedelta(days=10)

    async with session_factory() as session:
        session.add(ScheduleRule(project_id=None, rest_weekdays=[], effective_from=started))
        project = await session.get(Project, UUID(project_id))
        assert project is not None
        project.start_date = started
        project.created_business_date = started
        await session.commit()

    # Monday to Saturday are rest days, so only Sundays were ever expected.
    await client.put(
        f"{PROJECTS}/{project_id}/schedule",
        json={"rest_weekdays": [1, 2, 3, 4, 5, 6], "effective_from": started.isoformat()},
    )
    before = (await client.get(STATS)).json()["projects"][0]["expected_days"]

    cleared = await client.delete(f"{PROJECTS}/{project_id}/schedule")

    after = (await client.get(STATS)).json()["projects"][0]["expected_days"]
    assert cleared.json()["inherited"] is True
    # At most today joins the expected set; the ten settled days must not move.
    assert after == before + (0 if today.isoweekday() == 7 else 1)


async def test_after_clearing_the_project_follows_later_default_changes(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """The closed override inherits, so tomorrow's default change still reaches it."""
    await _login(client)
    response = await client.post(PROJECTS, json={"name": "Back to the fold"})
    project_id = response.json()["id"]
    today = today_business_date()
    await client.put(f"{PROJECTS}/{project_id}/schedule", json={"rest_weekdays": [1]})
    await client.delete(f"{PROJECTS}/{project_id}/schedule")

    async with session_factory() as session:
        session.add(ScheduleRule(project_id=None, rest_weekdays=[3], effective_from=today))
        await session.commit()

    body = (await client.get(f"{PROJECTS}/{project_id}/schedule")).json()

    assert body == {"rest_weekdays": [3], "effective_from": today.isoformat(), "inherited": True}

