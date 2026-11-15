from datetime import timedelta

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.clock import now_utc
from app.models.session import Session
from app.throttle import login_throttle
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

LOGIN = "/api/auth/login"
ME = "/api/auth/me"


async def _login(
    client: httpx.AsyncClient, password: str, email: str = ACCOUNT_EMAIL
) -> httpx.Response:
    return await client.post(LOGIN, json={"email": email, "password": password})


@pytest.fixture(autouse=True)
def _clean_throttle():
    login_throttle.reset()
    yield
    login_throttle.reset()


async def test_five_failures_lock_the_account_even_against_the_right_password(
    client: httpx.AsyncClient,
) -> None:
    for _ in range(5):
        assert (await _login(client, "wrong")).status_code == 401

    locked = await _login(client, ACCOUNT_PASSWORD)

    assert locked.status_code == 401
    assert locked.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_four_failures_do_not_lock(client: httpx.AsyncClient) -> None:
    for _ in range(4):
        assert (await _login(client, "wrong")).status_code == 401

    assert (await _login(client, ACCOUNT_PASSWORD)).status_code == 200


async def test_a_successful_login_clears_the_counter(client: httpx.AsyncClient) -> None:
    for _ in range(4):
        await _login(client, "wrong")

    assert (await _login(client, ACCOUNT_PASSWORD)).status_code == 200

    for _ in range(4):
        assert (await _login(client, "wrong")).status_code == 401

    # Eight failures in total, but the counter was cleared by the success.
    assert (await _login(client, ACCOUNT_PASSWORD)).status_code == 200


async def test_case_and_whitespace_do_not_create_a_second_identity(
    client: httpx.AsyncClient,
) -> None:
    variants = [
        ACCOUNT_EMAIL,
        ACCOUNT_EMAIL.upper(),
        f"  {ACCOUNT_EMAIL}  ",
        ACCOUNT_EMAIL.capitalize(),
        ACCOUNT_EMAIL.upper(),
    ]
    for email in variants:
        assert (await _login(client, "wrong", email=email)).status_code == 401

    assert (await _login(client, ACCOUNT_PASSWORD)).status_code == 401


async def test_the_lock_expires_after_fifteen_minutes(
    client: httpx.AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    for _ in range(5):
        await _login(client, "wrong")
    assert (await _login(client, ACCOUNT_PASSWORD)).status_code == 401

    later = now_utc() + timedelta(minutes=16)
    monkeypatch.setattr("app.throttle.now_utc", lambda: later)

    assert (await _login(client, ACCOUNT_PASSWORD)).status_code == 200


async def test_a_locked_response_is_indistinguishable_from_a_wrong_password(
    client: httpx.AsyncClient,
) -> None:
    wrong = await _login(client, "wrong")

    for _ in range(4):
        await _login(client, "wrong")
    locked = await _login(client, ACCOUNT_PASSWORD)

    assert locked.status_code == wrong.status_code
    assert locked.json() == wrong.json()
    assert set(locked.headers) == set(wrong.headers)


async def test_an_expired_session_is_rejected(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await _login(client, ACCOUNT_PASSWORD)

    async with session_factory() as session:
        row = await session.scalar(select(Session))
        assert row is not None
        row.expires_at = now_utc() - timedelta(minutes=1)
        await session.commit()

    response = await client.get(ME)

    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Session expired"
