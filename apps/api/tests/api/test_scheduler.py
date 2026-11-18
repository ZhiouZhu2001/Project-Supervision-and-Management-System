from datetime import UTC, datetime, time, timedelta

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.jobs.scheduler import ALERT_HOUR, JOB_ID, build_scheduler, catch_up
from app.models.alert import AlertLog
from app.models.schedule import ScheduleRule
from app.services.alerts import run_digest
from app.services.business_day import MADRID, today_business_date
from app.services.mail import RecordingMailer
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

PROJECTS = "/api/projects"
BASE_URL = "http://localhost:8080"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def _project(client: httpx.AsyncClient, name: str = "Write a little") -> str:
    return (await client.post(PROJECTS, json={"name": name})).json()["id"]


async def _no_rest_days(session_factory: async_sessionmaker[AsyncSession], since) -> None:
    async with session_factory() as session:
        session.add(ScheduleRule(project_id=None, rest_weekdays=[], effective_from=since))
        await session.commit()


def test_the_job_is_scheduled_at_2100_madrid() -> None:
    scheduler = build_scheduler(
        session_factory=None,  # type: ignore[arg-type]
        mailer=RecordingMailer(),
        to="o@example.com",
        base_url=BASE_URL,
    )

    job = scheduler.get_job(JOB_ID)

    assert job is not None
    trigger = job.trigger
    assert ALERT_HOUR == 21
    assert "hour='21'" in str(trigger)
    assert str(trigger.timezone) == "Europe/Madrid"


async def test_a_restart_after_2100_still_judges_the_day(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    await _project(client, "Evening")
    today = today_business_date()
    await _no_rest_days(session_factory, today)
    mailer = RecordingMailer()
    after_2100 = datetime.combine(today, time(21, 30), tzinfo=MADRID).astimezone(UTC)

    handled = await catch_up(
        session_factory=session_factory,
        mailer=mailer,
        to="o@example.com",
        base_url=BASE_URL,
        at=after_2100,
    )

    assert handled is True
    assert len(mailer.sent) == 1


async def test_a_restart_before_2100_leaves_the_evening_alone(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    await _project(client, "Morning")
    today = today_business_date()
    await _no_rest_days(session_factory, today)
    mailer = RecordingMailer()
    before_2100 = datetime.combine(today, time(9, 0), tzinfo=MADRID).astimezone(UTC)

    handled = await catch_up(
        session_factory=session_factory,
        mailer=mailer,
        to="o@example.com",
        base_url=BASE_URL,
        at=before_2100,
    )

    assert handled is False
    assert mailer.sent == []


async def test_a_restart_after_a_sent_digest_does_not_resend(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    await _project(client, "Evening")
    today = today_business_date()
    await _no_rest_days(session_factory, today)
    mailer = RecordingMailer()
    after_2100 = datetime.combine(today, time(22, 0), tzinfo=MADRID).astimezone(UTC)

    first = await catch_up(
        session_factory=session_factory,
        mailer=mailer,
        to="o@example.com",
        base_url=BASE_URL,
        at=after_2100,
    )
    second = await catch_up(
        session_factory=session_factory,
        mailer=mailer,
        to="o@example.com",
        base_url=BASE_URL,
        at=after_2100,
    )

    assert first is True
    assert second is False
    assert len(mailer.sent) == 1


async def test_the_health_endpoint_reports_the_last_judged_day(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    before = (await client.get("/api/healthz")).json()
    assert "last_alert_business_date" in before

    async with session_factory() as session:
        await run_digest(
            session,
            RecordingMailer(),
            to="o@example.com",
            current=today_business_date(),
            base_url=BASE_URL,
        )

    after = (await client.get("/api/healthz")).json()
    assert after["last_alert_business_date"] == today_business_date().isoformat()


async def test_an_old_row_does_not_count_as_todays_work(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    today = today_business_date()
    async with session_factory() as session:
        session.add(
            AlertLog(business_date=today - timedelta(days=1), status="no_misses", project_count=0)
        )
        await session.commit()

    health = (await client.get("/api/healthz")).json()

    # The stale date is exactly what makes a dead scheduler visible.
    assert health["last_alert_business_date"] == (today - timedelta(days=1)).isoformat()


async def test_only_one_project_row_per_business_day(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    await _project(client, "Evening")
    today = today_business_date()
    await _no_rest_days(session_factory, today)
    mailer = RecordingMailer()

    async with session_factory() as session:
        await run_digest(session, mailer, to="o@example.com", current=today, base_url=BASE_URL)
        await run_digest(session, mailer, to="o@example.com", current=today, base_url=BASE_URL)
        rows = await session.scalar(select(func.count()).select_from(AlertLog))

    assert rows == 1


async def test_a_finished_project_is_never_a_candidate(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client, "Done and dusted")
    today = today_business_date()
    await _no_rest_days(session_factory, today)
    await client.patch(f"{PROJECTS}/{project_id}/status", json={"status": "finished"})
    mailer = RecordingMailer()

    async with session_factory() as session:
        report = await run_digest(
            session, mailer, to="o@example.com", current=today, base_url=BASE_URL
        )

    assert report.status == "no_misses"
    assert mailer.sent == []


async def test_the_database_records_every_judgement(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = await _project(client, "Quiet")
    await client.post("/api/logs", json={"project_id": project_id, "content": "done"})
    today = today_business_date()
    await _no_rest_days(session_factory, today)

    async with session_factory() as session:
        await run_digest(
            session, RecordingMailer(), to="o@example.com", current=today, base_url=BASE_URL
        )
        session.add(
            AlertLog(business_date=today - timedelta(days=1), status="sent", project_count=1)
        )
        await session.commit()

        statuses = list(
            await session.scalars(select(AlertLog.status).order_by(AlertLog.business_date))
        )

    assert statuses == ["sent", "no_misses"]

async def test_a_restart_after_midnight_still_judges_the_business_day(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    """At 00:30 the business day is still yesterday, and its 21:00 has passed.

    Judging by the wall clock's hour would skip the day entirely and leave it
    unjudged until the following evening.
    """
    await _login(client)
    await _project(client, "Evening")
    today = today_business_date()
    await _no_rest_days(session_factory, today)
    mailer = RecordingMailer()
    after_midnight = datetime.combine(today + timedelta(days=1), time(0, 30), tzinfo=MADRID).astimezone(
        UTC
    )

    handled = await catch_up(
        session_factory=session_factory,
        mailer=mailer,
        to="o@example.com",
        base_url=BASE_URL,
        at=after_midnight,
    )

    assert handled is True
    assert len(mailer.sent) == 1
    async with session_factory() as session:
        judged = await session.scalar(select(AlertLog.business_date))
    assert judged == today
