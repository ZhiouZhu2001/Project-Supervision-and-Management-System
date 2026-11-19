import io
import re
from uuid import UUID

import httpx
import pytest
from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.models.attachment import Attachment
from app.models.log import Log
from app.services.storage import MAX_BYTES
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

PROJECTS = "/api/projects"
LOGS = "/api/logs"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def _log(client: httpx.AsyncClient, project_id: str) -> str:
    created = await client.post(LOGS, json={"project_id": project_id, "content": "with a picture"})
    assert created.status_code == 201
    return created.json()["id"]


def _image_bytes(
    fmt: str = "PNG", size: tuple[int, int] = (40, 30), colour: str = "#b84c25"
) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, colour).save(buffer, format=fmt)
    return buffer.getvalue()


async def _project(client: httpx.AsyncClient) -> str:
    return (await client.post(PROJECTS, json={"name": "Write a little"})).json()["id"]


async def test_a_png_can_be_attached(client: httpx.AsyncClient) -> None:
    await _login(client)
    log_id = await _log(client, await _project(client))

    response = await client.post(
        f"{LOGS}/{log_id}/attachments",
        files={"file": ("shot.png", _image_bytes(), "image/png")},
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["width"] == 40
    assert body["height"] == 30
    assert body["content_type"] == "image/png"
    assert body["url"] == f"/api/attachments/{body['id']}"


async def test_the_type_comes_from_the_bytes_not_the_name(client: httpx.AsyncClient) -> None:
    await _login(client)
    log_id = await _log(client, await _project(client))

    # A JPEG delivered with a lying filename and content type.
    response = await client.post(
        f"{LOGS}/{log_id}/attachments",
        files={"file": ("photo.png", _image_bytes("JPEG"), "image/png")},
    )

    assert response.status_code == 201
    assert response.json()["content_type"] == "image/jpeg"


async def test_a_non_image_is_refused(client: httpx.AsyncClient) -> None:
    await _login(client)
    log_id = await _log(client, await _project(client))

    response = await client.post(
        f"{LOGS}/{log_id}/attachments",
        files={"file": ("notreally.png", b"this is plain text", "image/png")},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ATTACHMENT_TYPE_UNSUPPORTED"


async def test_an_oversized_image_is_refused(client: httpx.AsyncClient) -> None:
    await _login(client)
    log_id = await _log(client, await _project(client))

    oversized = b"\x89PNG\r\n\x1a\n" + b"0" * (MAX_BYTES + 10)
    response = await client.post(
        f"{LOGS}/{log_id}/attachments",
        files={"file": ("big.png", oversized, "image/png")},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ATTACHMENT_TOO_LARGE"


async def test_a_fifth_image_is_refused_and_the_first_four_survive(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)
    project_id = await _project(client)
    log_id = await _log(client, project_id)
    for index in range(4):
        created = await client.post(
            f"{LOGS}/{log_id}/attachments",
            files={"file": (f"{index}.png", _image_bytes(), "image/png")},
        )
        assert created.status_code == 201

    fifth = await client.post(
        f"{LOGS}/{log_id}/attachments",
        files={"file": ("fifth.png", _image_bytes(), "image/png")},
    )

    assert fifth.status_code == 422
    assert fifth.json()["error"]["code"] == "ATTACHMENT_LIMIT_REACHED"
    listed = (await client.get(LOGS, params={"project_id": project_id})).json()
    assert len(listed[0]["attachments"]) == 4


async def test_serving_requires_a_session(client: httpx.AsyncClient) -> None:
    await _login(client)
    log_id = await _log(client, await _project(client))
    created = await client.post(
        f"{LOGS}/{log_id}/attachments",
        files={"file": ("shot.png", _image_bytes(), "image/png")},
    )
    url = created.json()["url"]

    saved = dict(client.cookies)
    client.cookies.clear()
    response = await client.get(url)
    client.cookies.update(saved)

    assert response.status_code == 401


async def test_serving_hands_the_file_to_the_proxy(client: httpx.AsyncClient) -> None:
    await _login(client)
    log_id = await _log(client, await _project(client))
    created = await client.post(
        f"{LOGS}/{log_id}/attachments",
        files={"file": ("shot.png", _image_bytes(), "image/png")},
    )

    response = await client.get(created.json()["url"])

    assert response.status_code == 200
    redirect = response.headers["x-accel-redirect"]
    key = redirect.removeprefix("/protected/")
    # ARCH 8: YYYY/MM/<ulid>.<ext> — the original name never reaches the disk.
    assert re.fullmatch(r"\d{4}/\d{2}/[0-9A-HJKMNP-TV-Z]{26}\.png", key), key
    assert "shot" not in redirect


async def test_the_stored_file_exists_and_is_removed_on_delete(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    log_id = await _log(client, await _project(client))
    created = await client.post(
        f"{LOGS}/{log_id}/attachments",
        files={"file": ("shot.png", _image_bytes(), "image/png")},
    )
    attachment_id = UUID(created.json()["id"])

    async with session_factory() as session:
        stored = await session.get(Attachment, attachment_id)
        assert stored is not None
        path = stored.storage_key

    from pathlib import Path

    on_disk = Path(get_settings().upload_dir) / path
    assert on_disk.exists()

    assert (await client.delete(f"/api/attachments/{attachment_id}")).status_code == 204

    assert not on_disk.exists()
    async with session_factory() as session:
        assert await session.get(Attachment, attachment_id) is None
    assert (await client.get(created.json()["url"])).status_code == 404


async def test_attachments_belong_to_their_log_in_the_list(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    log_id = await _log(client, project_id)
    await client.post(
        f"{LOGS}/{log_id}/attachments",
        files={"file": ("shot.png", _image_bytes(), "image/png")},
    )

    listed = (await client.get(LOGS, params={"project_id": project_id})).json()

    assert len(listed[0]["attachments"]) == 1
    assert listed[0]["attachments"][0]["id"]


async def test_a_deleted_log_hides_its_images(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client)
    log_id = await _log(client, await _project(client))
    created = await client.post(
        f"{LOGS}/{log_id}/attachments",
        files={"file": ("shot.png", _image_bytes(), "image/png")},
    )

    await client.delete(f"{LOGS}/{log_id}")

    # The row survives so a restore keeps the picture, but the image is not
    # reachable while the log is deleted.
    assert (await client.get(created.json()["url"])).status_code == 404


async def test_only_image_types_are_accepted_by_the_decoder() -> None:
    from app.services.storage import UnsupportedImage, inspect_image

    with pytest.raises(UnsupportedImage):
        inspect_image(b"\x00\x01\x02")


async def test_purging_a_log_removes_its_files(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    from datetime import UTC, datetime, timedelta
    from pathlib import Path

    from app.jobs.purge import purge_expired

    await _login(client)
    log_id = UUID(await _log(client, await _project(client)))
    created = await client.post(
        f"{LOGS}/{log_id}/attachments",
        files={"file": ("shot.png", _image_bytes(), "image/png")},
    )
    assert created.status_code == 201

    async with session_factory() as session:
        stored = await session.get(Attachment, UUID(created.json()["id"]))
        assert stored is not None
        on_disk = Path(get_settings().upload_dir) / stored.storage_key
        assert on_disk.exists()

    await client.delete(f"{LOGS}/{log_id}")

    async with session_factory() as session:
        log = await session.get(Log, log_id)
        assert log is not None
        log.deleted_at = datetime.now(UTC) - timedelta(days=31)
        await session.commit()

        report = await purge_expired(session)
        remaining = await session.scalar(select(func.count()).select_from(Attachment))

    assert report.logs == 1
    assert report.files == 1
    assert remaining == 0
    assert not on_disk.exists()



