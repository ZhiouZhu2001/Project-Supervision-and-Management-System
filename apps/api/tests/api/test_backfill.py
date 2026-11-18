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
CALENDAR = "/api/calendar"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def _backdated_project(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession], days: int
) -> str:
    """A project that has existed for `days`, so its past days are recordable."""
    project_id = (await client.post(PROJECTS, json={"name": "Long running"})).json()["id"]
    start = today_business_date() - timedelta(days=days)
    async with session_factory() as session:
        project = await session.get(Project, UUID(project_id))
        assert project is not None
        project.start_date = start
        project.created_business_date = start
        await session.commit()
    return project_id


def _day(days_ago: int) -> str:
    return (today_business_date() - timedelta(days=days_ago)).isoformat()


async def test_a_day_within_the_window_is_accepted_and_marked_backfilled(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _backdated_project(client, session_factory, 10)

    response = await client.post(
        LOGS, json={"project_id": project_id, "content": "remembered", "business_date": _day(3)}
    )

    assert response.status_code == 201
    assert response.json()["backfilled"] is True
    assert response.json()["business_date"] == _day(3)


async def test_a_day_eight_days_old_is_refused(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _backdated_project(client, session_factory, 20)

    response = await client.post(
        LOGS, json={"project_id": project_id, "content": "too late", "business_date": _day(8)}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "BUSINESS_DATE_TOO_OLD"


async def test_the_seventh_day_back_is_still_open(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _backdated_project(client, session_factory, 20)

    response = await client.post(
        LOGS, json={"project_id": project_id, "content": "edge", "business_date": _day(7)}
    )

    assert response.status_code == 201


async def test_three_backfills_are_allowed_and_the_fourth_is_refused(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _backdated_project(client, session_factory, 10)
    payload = {"project_id": project_id, "business_date": _day(2)}

    for index in range(3):
        created = await client.post(LOGS, json={**payload, "content": f"part {index}"})
        assert created.status_code == 201, created.text

    fourth = await client.post(LOGS, json={**payload, "content": "one too many"})

    assert fourth.status_code == 422
    assert fourth.json()["error"]["code"] == "BACKFILL_LIMIT_REACHED"


async def test_the_cap_is_per_project_and_per_day(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    first = await _backdated_project(client, session_factory, 10)
    second = await _backdated_project(client, session_factory, 10)
    for index in range(3):
        await client.post(
            LOGS, json={"project_id": first, "content": f"a{index}", "business_date": _day(2)}
        )

    other_day = await client.post(
        LOGS, json={"project_id": first, "content": "another day", "business_date": _day(3)}
    )
    other_project = await client.post(
        LOGS, json={"project_id": second, "content": "another project", "business_date": _day(2)}
    )

    assert other_day.status_code == 201
    assert other_project.status_code == 201


async def test_backfill_status_reports_what_is_left(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _backdated_project(client, session_factory, 10)

    before = (
        await client.get(
            f"{LOGS}/backfill-status",
            params={"project_id": project_id, "business_date": _day(2)},
        )
    ).json()
    await client.post(
        LOGS, json={"project_id": project_id, "content": "one", "business_date": _day(2)}
    )
    after = (
        await client.get(
            f"{LOGS}/backfill-status",
            params={"project_id": project_id, "business_date": _day(2)},
        )
    ).json()

    assert before == {"limit": 3, "used": 0, "remaining": 3, "allowed": True}
    assert after["remaining"] == 2
    assert after["used"] == 1


async def test_a_backfilled_log_does_not_repair_the_streak(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _backdated_project(client, session_factory, 10)
    before = (await client.get(TODAY)).json()["projects"][0]["current_streak"]

    await client.post(
        LOGS,
        json={
            "project_id": project_id,
            "content": "yesterday, remembered",
            "business_date": _day(1),
        },
    )
    await client.post(
        LOGS, json={"project_id": project_id, "content": "and today", "business_date": _day(0)}
    )

    after = (await client.get(TODAY)).json()["projects"][0]

    assert before == 0
    # Today counts, yesterday's backfill does not: the chain is one day long,
    # not two.
    assert after["current_streak"] == 1


async def test_the_calendar_marks_days_written_later(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _backdated_project(client, session_factory, 10)
    await client.post(
        LOGS, json={"project_id": project_id, "content": "later", "business_date": _day(1)}
    )

    body = (await client.get(CALENDAR)).json()
    days = {entry["business_date"]: entry for entry in body["days"]}

    assert days[_day(1)]["backfilled_count"] == 1
    assert days[_day(0)]["backfilled_count"] == 0
