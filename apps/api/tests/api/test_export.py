from datetime import date, timedelta
from uuid import UUID

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.log import Log
from app.models.project import Project
from app.models.schedule import ScheduleRule
from app.services.business_day import today_business_date
from app.services.streak import current_streak, expected_days
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

EXPORT = "/api/export.json"
PROJECTS = "/api/projects"
LOGS = "/api/logs"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def test_an_empty_account_exports_a_valid_document(client: httpx.AsyncClient) -> None:
    await _login(client)

    response = await client.get(EXPORT)

    assert response.status_code == 200
    body = response.json()
    assert body["export_version"] == 1
    assert body["projects"] == []
    assert body["logs"] == []


async def test_the_export_contains_every_collection(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = (await client.post(PROJECTS, json={"name": "Write a little"})).json()["id"]
    log = await client.post(
        LOGS, json={"project_id": project_id, "content": "with a tag", "tags": ["deep"]}
    )

    body = (await client.get(EXPORT)).json()

    assert set(body) == {
        "export_version",
        "exported_at",
        "account",
        "projects",
        "logs",
        "attachments",
        "schedule_rules",
        "project_status_changes",
    }
    assert body["logs"][0]["tags"] == ["deep"]
    assert body["project_status_changes"][0]["status"] == "active"
    assert log.status_code == 201


async def test_the_export_carries_no_authentication_material(client: httpx.AsyncClient) -> None:
    await _login(client)
    await client.post(PROJECTS, json={"name": "Write a little"})

    raw = (await client.get(EXPORT)).text.lower()

    assert "password" not in raw
    assert "token" not in raw
    assert "argon2" not in raw
    assert "session" not in raw


async def test_attachment_metadata_has_a_checksum_and_no_bytes(
    client: httpx.AsyncClient,
) -> None:
    import io

    from PIL import Image

    await _login(client)
    project_id = (await client.post(PROJECTS, json={"name": "Write a little"})).json()["id"]
    log_id = (await client.post(LOGS, json={"project_id": project_id, "content": "x"})).json()["id"]
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "#b84c25").save(buffer, format="PNG")
    await client.post(
        f"{LOGS}/{log_id}/attachments",
        files={"file": ("shot.png", buffer.getvalue(), "image/png")},
    )

    body = (await client.get(EXPORT)).json()

    attachment = body["attachments"][0]
    assert len(attachment["sha256"]) == 64
    assert attachment["bytes_included"] is False
    assert "content" not in attachment


async def test_the_export_is_enough_to_rebuild_the_streak(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    project_id = (await client.post(PROJECTS, json={"name": "Rebuildable"})).json()["id"]
    today = today_business_date()

    async with session_factory() as session:
        session.add(
            ScheduleRule(
                project_id=None, rest_weekdays=[], effective_from=today - timedelta(days=9)
            )
        )
        project = await session.get(Project, UUID(project_id))
        assert project is not None
        project.start_date = today - timedelta(days=2)
        project.created_business_date = today - timedelta(days=2)
        # Written on the day, not backfilled: a streak is made of those.
        for offset in (1, 0):
            session.add(
                Log(
                    project_id=UUID(project_id),
                    business_date=today - timedelta(days=offset),
                    content="done",
                    backfilled=False,
                )
            )
        await session.commit()

    live = (await client.get("/api/stats")).json()["projects"][0]["current_streak"]

    body = (await client.get(EXPORT)).json()

    # Recompute from the document alone, with the same kernel a fresh install
    # would use: expected days come from the imported rules and start date,
    # checked days from the imported logs.
    project_row = body["projects"][0]
    rest_days = body["schedule_rules"][0]["rest_weekdays"]
    start = date.fromisoformat(project_row["start_date"])
    days = expected_days(start, today, rest_weekdays=frozenset(rest_days))
    checked = {
        date.fromisoformat(log["business_date"]) for log in body["logs"] if not log["backfilled"]
    }
    rebuilt = current_streak(days, checked, today)

    assert start == today - timedelta(days=2)
    assert rebuilt == live == 2
