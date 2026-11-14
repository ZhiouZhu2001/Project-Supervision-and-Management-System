import httpx
import pytest

from app.main import create_app


@pytest.fixture
def app():
    return create_app()


async def _get_healthz(app) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.get("/api/healthz")


async def test_healthz_is_ok_and_unauthenticated_when_the_database_answers(
    app, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def reachable() -> bool:
        return True

    monkeypatch.setattr("app.main.check_database", reachable)

    response = await _get_healthz(app)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] is True
    assert body["version"]
    assert body["time"].endswith("+00:00")


async def test_healthz_fails_loudly_when_the_database_does_not_answer(
    app, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def unreachable() -> bool:
        return False

    monkeypatch.setattr("app.main.check_database", unreachable)

    response = await _get_healthz(app)

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["db"] is False


async def test_openapi_and_docs_are_not_exposed(app) -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        assert (await client.get("/docs")).status_code == 404
        assert (await client.get("/openapi.json")).status_code == 404
