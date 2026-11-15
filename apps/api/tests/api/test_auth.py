import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap import ensure_account
from app.models.account import Account
from app.models.session import Session
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

LOGIN = "/api/auth/login"
ME = "/api/auth/me"
LOGOUT = "/api/auth/logout"


async def test_login_sets_an_httponly_session_cookie(client: httpx.AsyncClient) -> None:
    response = await client.post(LOGIN, json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD})

    assert response.status_code == 200
    assert response.json()["email"] == ACCOUNT_EMAIL

    cookie = response.headers["set-cookie"]
    assert "sid=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie.replace("samesite=lax", "SameSite=lax")
    # Secure is deliberately absent in development, where the origin is http.
    assert "Secure" not in cookie


async def test_me_returns_the_account_for_a_valid_session(client: httpx.AsyncClient) -> None:
    await client.post(LOGIN, json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD})

    response = await client.get(ME)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == ACCOUNT_EMAIL
    assert body["timezone"] == "Europe/Madrid"


async def test_a_wrong_password_is_rejected_with_the_standard_error_shape(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(LOGIN, json={"email": ACCOUNT_EMAIL, "password": "wrong"})

    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "INVALID_CREDENTIALS"
    assert set(body["error"]) == {"code", "message", "details"}


async def test_an_unknown_email_is_indistinguishable_from_a_wrong_password(
    client: httpx.AsyncClient,
) -> None:
    response = await client.post(LOGIN, json={"email": "nobody@example.com", "password": "wrong"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


async def test_me_without_a_session_is_unauthenticated(client: httpx.AsyncClient) -> None:
    response = await client.get(ME)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_an_invalid_email_address_is_a_validation_error(client: httpx.AsyncClient) -> None:
    response = await client.post(LOGIN, json={"email": "not-an-email", "password": "x"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_logout_deletes_the_session_server_side(client: httpx.AsyncClient) -> None:
    await client.post(LOGIN, json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD})
    assert (await client.get(ME)).status_code == 200

    assert (await client.post(LOGOUT)).status_code == 204

    assert (await client.get(ME)).status_code == 401


async def test_replaying_a_cookie_from_a_deleted_session_is_rejected(
    client: httpx.AsyncClient,
) -> None:
    login = await client.post(LOGIN, json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD})
    replayed = login.cookies["sid"]
    await client.post(LOGOUT)

    client.cookies.set("sid", replayed)
    replay = await client.get(ME)

    assert replay.status_code == 401


async def test_logout_all_invalidates_every_session(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await client.post(LOGIN, json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD})
    first = client.cookies["sid"]
    await client.post(LOGIN, json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD})
    second = client.cookies["sid"]
    assert first != second

    assert (await client.post("/api/auth/logout-all")).status_code == 204

    client.cookies.set("sid", first)
    assert (await client.get(ME)).status_code == 401

    client.cookies.set("sid", second)
    assert (await client.get(ME)).status_code == 401


async def test_a_foreign_origin_is_rejected_on_writes(client: httpx.AsyncClient) -> None:
    response = await client.post(
        LOGIN,
        json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD},
        headers={"origin": "https://evil.example"},
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ORIGIN_REJECTED"


async def test_the_same_origin_is_accepted_on_writes(client: httpx.AsyncClient) -> None:
    response = await client.post(
        LOGIN,
        json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD},
        headers={"origin": "http://localhost:8080"},
    )

    assert response.status_code == 200


async def test_the_loopback_spelling_is_the_same_origin(client: httpx.AsyncClient) -> None:
    # Opening the app at 127.0.0.1 instead of localhost must not break writes:
    # the browser's origin matches the Host it sent, which is what matters.
    response = await client.post(
        LOGIN,
        json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD},
        headers={"host": "127.0.0.1:8080", "origin": "http://127.0.0.1:8080"},
    )

    assert response.status_code == 200


async def test_a_foreign_origin_cannot_borrow_the_host_header(client: httpx.AsyncClient) -> None:
    response = await client.post(
        LOGIN,
        json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD},
        headers={"host": "localhost:8080", "origin": "http://evil.example"},
    )

    assert response.status_code == 403


async def test_the_password_is_never_stored_in_plain_text(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    async with session_factory() as session:
        stored = await session.scalar(select(Account.password_hash))

    assert stored is not None
    assert stored.startswith("$argon2id$")
    assert ACCOUNT_PASSWORD not in stored


async def test_only_a_hash_of_the_session_token_is_stored(
    client: httpx.AsyncClient, session_factory: async_sessionmaker[AsyncSession]
) -> None:
    await client.post(LOGIN, json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD})
    token = client.cookies["sid"]

    async with session_factory() as session:
        hashes = list(await session.scalars(select(Session.token_hash)))

    assert token not in hashes
    assert all(len(value) == 64 for value in hashes)


@pytest.mark.parametrize("password", [ACCOUNT_PASSWORD, "wrong"])
async def test_seeding_is_idempotent(
    session_factory: async_sessionmaker[AsyncSession], account: None, password: str
) -> None:
    async with session_factory() as session:
        created = await ensure_account(session, email=ACCOUNT_EMAIL, password=password)
        await session.commit()
        total = await session.scalar(select(func.count()).select_from(Account))

    assert created is False
    assert total == 1
