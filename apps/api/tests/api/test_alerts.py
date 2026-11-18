from datetime import timedelta
from uuid import UUID

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.alert import AlertLog
from app.models.log import Log
from app.models.project import Project
from app.models.schedule import ScheduleRule
from app.models.status import ProjectStatusChange
from app.services.alerts import run_digest
from app.services.business_day import today_business_date
from app.services.mail import RecordingMailer
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

PROJECTS = "/api/projects"
LOGS = "/api/logs"
BASE_URL = "http://localhost:8080"


class BrokenMailer:
    def send(self, *, to: str, subject: str, body: str) -> None:
        raise OSError("smtp is down")


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def _project(client: httpx.AsyncClient, name: str) -> str:
    return (await client.post(PROJECTS, json={"name": name})).json()["id"]


async def _no_rest_days(session_factory: async_sessionmaker[AsyncSession], since) -> None:
    async with session_factory() as session:
        session.add(ScheduleRule(project_id=None, rest_weekdays=[], effective_from=since))
        await session.commit()


async def test_a_missed_project_produces_one_email(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    await _project(client, "Write a little")
    today = today_business_date()
    await _no_rest_days(session_factory, today)
    mailer = RecordingMailer()

    async with session_factory() as session:
        report = await run_digest(
            session, mailer, to="owner@example.com", current=today, base_url=BASE_URL
        )

    assert report.status == "sent"
    assert report.project_count == 1
    assert len(mailer.sent) == 1
    assert "Write a little" in mailer.sent[0].body
    assert str(today) in mailer.sent[0].body


async def test_a_recorded_project_is_not_in_the_digest(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client, "Recorded")
    await _project(client, "Forgotten")
    today = today_business_date()
    await _no_rest_days(session_factory, today)
    await client.post(LOGS, json={"project_id": project_id, "content": "done today"})
    mailer = RecordingMailer()

    async with session_factory() as session:
        await run_digest(session, mailer, to="o@example.com", current=today, base_url=BASE_URL)

    assert len(mailer.sent) == 1
    assert "Forgotten" in mailer.sent[0].body
    assert "Recorded" not in mailer.sent[0].body


async def test_nothing_missed_sends_nothing(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    today = today_business_date()
    await _no_rest_days(session_factory, today)
    mailer = RecordingMailer()

    async with session_factory() as session:
        report = await run_digest(
            session, mailer, to="o@example.com", current=today, base_url=BASE_URL
        )
        rows = list(await session.scalars(select(AlertLog)))

    assert report.status == "no_misses"
    assert mailer.sent == []
    # The decision is still recorded, so a quiet day and a dead scheduler differ.
    assert [row.status for row in rows] == ["no_misses"]


async def test_paused_and_archived_projects_never_appear(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    paused = await _project(client, "Paused one")
    archived = await _project(client, "Archived one")
    await _project(client, "Live one")
    await client.patch(f"{PROJECTS}/{paused}/status", json={"status": "paused"})
    await client.patch(f"{PROJECTS}/{archived}/status", json={"status": "archived"})
    today = today_business_date()
    await _no_rest_days(session_factory, today)
    mailer = RecordingMailer()

    async with session_factory() as session:
        await run_digest(session, mailer, to="o@example.com", current=today, base_url=BASE_URL)

    body = mailer.sent[0].body
    assert "Live one" in body
    assert "Paused one" not in body
    assert "Archived one" not in body


async def test_the_entry_carries_streak_missed_days_and_a_link(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client, "Steady")
    today = today_business_date()
    # The rest-day rule must predate the fixture days, or the weekend default
    # would remove some of them from the expected set.
    await _no_rest_days(session_factory, today - timedelta(days=10))

    async with session_factory() as session:
        project = await session.get(Project, UUID(project_id))
        assert project is not None
        project.start_date = today - timedelta(days=3)
        project.created_business_date = today - timedelta(days=3)
        status = await session.scalar(
            select(ProjectStatusChange).where(ProjectStatusChange.project_id == UUID(project_id))
        )
        if status is not None:
            status.effective_from = today - timedelta(days=3)
        # Three good days ending yesterday, nothing written today.
        for offset in (3, 2, 1):
            session.add(
                Log(
                    project_id=UUID(project_id),
                    business_date=today - timedelta(days=offset),
                    content="done",
                    backfilled=False,
                )
            )
        await session.commit()

    mailer = RecordingMailer()
    async with session_factory() as session:
        await run_digest(session, mailer, to="o@example.com", current=today, base_url=BASE_URL)

    body = mailer.sent[0].body
    assert "3 day streak" in body
    assert "first missed day" in body
    assert f"{BASE_URL}/projects/{project_id}" in body


async def test_running_twice_in_a_day_sends_once(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    await _project(client, "Write a little")
    today = today_business_date()
    await _no_rest_days(session_factory, today)
    mailer = RecordingMailer()

    async with session_factory() as session:
        first = await run_digest(
            session, mailer, to="o@example.com", current=today, base_url=BASE_URL
        )
        second = await run_digest(
            session, mailer, to="o@example.com", current=today, base_url=BASE_URL
        )
        count = await session.scalar(select(func.count()).select_from(AlertLog))

    assert first.status == "sent"
    assert second.status == "skipped"
    assert len(mailer.sent) == 1
    assert count == 1


async def test_a_mail_failure_is_recorded_and_swallowed(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    await _project(client, "Write a little")
    today = today_business_date()
    await _no_rest_days(session_factory, today)

    async with session_factory() as session:
        report = await run_digest(
            session, BrokenMailer(), to="o@example.com", current=today, base_url=BASE_URL
        )
        row = await session.scalar(select(AlertLog))

    assert report.status == "failed"
    assert report.detail is not None
    assert row is not None
    assert row.status == "failed"
    assert "smtp is down" in (row.detail or "")


async def test_paused_projects_do_not_count_as_missed_even_on_a_workday(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client, "Paused today")
    today = today_business_date()
    await _no_rest_days(session_factory, today)
    await client.patch(f"{PROJECTS}/{project_id}/status", json={"status": "paused"})
    mailer = RecordingMailer()

    async with session_factory() as session:
        report = await run_digest(
            session, mailer, to="o@example.com", current=today, base_url=BASE_URL
        )

    assert report.status == "no_misses"
    assert mailer.sent == []
