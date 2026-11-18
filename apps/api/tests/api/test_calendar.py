import calendar as month_calendar
from datetime import date, timedelta
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.project import Project
from app.models.schedule import ScheduleRule
from app.services.business_day import today_business_date
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

CALENDAR = "/api/calendar"
PROJECTS = "/api/projects"
LOGS = "/api/logs"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def _no_rest_days(session_factory: async_sessionmaker[AsyncSession], since: date) -> None:
    """Weekends would otherwise make month-level assertions weekday-dependent."""
    async with session_factory() as session:
        session.add(ScheduleRule(project_id=None, rest_weekdays=[], effective_from=since))
        await session.commit()


async def _backdate(
    session_factory: async_sessionmaker[AsyncSession], project_id: str, since: date
) -> None:
    async with session_factory() as session:
        project = await session.get(Project, UUID(project_id))
        assert project is not None
        project.start_date = since
        project.created_business_date = since
        await session.commit()


async def _project(client: httpx.AsyncClient, name: str = "Write a little") -> str:
    return (await client.post(PROJECTS, json={"name": name})).json()["id"]


def _days_by_date(body: dict) -> dict[str, dict]:
    return {entry["business_date"]: entry for entry in body["days"]}


async def test_a_bad_month_is_rejected(client: httpx.AsyncClient) -> None:
    await _login(client)

    response = await client.get(CALENDAR, params={"month": "November"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "MONTH_INVALID"


async def test_the_calendar_covers_the_whole_month(client: httpx.AsyncClient) -> None:
    await _login(client)

    body = (await client.get(CALENDAR, params={"month": "2026-11"})).json()

    assert body["month"] == "2026-11"
    assert len(body["days"]) == month_calendar.monthrange(2026, 11)[1]
    assert body["days"][0]["business_date"] == "2026-11-01"
    assert body["days"][-1]["business_date"] == "2026-11-30"


async def test_days_after_today_are_inactive(client: httpx.AsyncClient) -> None:
    await _login(client)
    today = today_business_date()

    body = (await client.get(CALENDAR, params={"month": today.strftime("%Y-%m")})).json()
    days = _days_by_date(body)

    tomorrow = today + timedelta(days=1)
    if tomorrow.month == today.month:
        assert days[tomorrow.isoformat()]["state"] == "future"


async def test_a_rest_day_is_neutral_rather_than_a_failure(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    today = today_business_date()
    await _project(client)

    body = (await client.get(CALENDAR, params={"month": today.strftime("%Y-%m")})).json()
    days = _days_by_date(body)
    weekend = next(day for day, entry in days.items() if date.fromisoformat(day).isoweekday() >= 6)
    entry = days[weekend]
    if entry["state"] != "future":
        # Default rule: Saturday and Sunday are rest days with nothing expected.
        assert entry["expected_count"] == 0
        assert entry["state"] == "rest"


async def test_a_recorded_day_is_full_and_an_empty_day_is_none(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    today = today_business_date()
    month_start = today.replace(day=1)
    project_id = await _project(client)
    await _backdate(session_factory, project_id, month_start)
    await _no_rest_days(session_factory, month_start)
    await client.post(LOGS, json={"project_id": project_id, "content": "today"})

    body = (await client.get(CALENDAR, params={"month": today.strftime("%Y-%m")})).json()
    days = _days_by_date(body)

    assert days[today.isoformat()]["state"] == "all"
    assert days[today.isoformat()]["done_count"] == 1
    yesterday = today - timedelta(days=1)
    assert days[yesterday.isoformat()]["state"] == "none"


async def test_partial_days_reflect_how_many_projects_were_recorded(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    today = today_business_date()
    month_start = today.replace(day=1)
    ids = [await _project(client, f"Project {index}") for index in range(3)]
    for project_id in ids:
        await _backdate(session_factory, project_id, month_start)
    await _no_rest_days(session_factory, month_start)

    await client.post(LOGS, json={"project_id": ids[0], "content": "one"})
    body_one = _days_by_date(
        (await client.get(CALENDAR, params={"month": today.strftime("%Y-%m")})).json()
    )
    assert body_one[today.isoformat()]["state"] == "partial"

    await client.post(LOGS, json={"project_id": ids[1], "content": "two"})
    body_two = _days_by_date(
        (await client.get(CALENDAR, params={"month": today.strftime("%Y-%m")})).json()
    )
    assert body_two[today.isoformat()]["state"] == "most"
