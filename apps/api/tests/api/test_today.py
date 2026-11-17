import httpx

from app.services.business_day import DAY_CUTOVER_HOUR, today_business_date
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

TODAY = "/api/today"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def test_today_requires_a_session(client: httpx.AsyncClient) -> None:
    assert (await client.get(TODAY)).status_code == 401


async def test_today_returns_the_server_side_business_date(client: httpx.AsyncClient) -> None:
    await _login(client)

    response = await client.get(TODAY)

    assert response.status_code == 200
    body = response.json()
    assert body["business_date"] == today_business_date().isoformat()
    assert body["timezone"] == "Europe/Madrid"
    assert body["cutover_hour"] == DAY_CUTOVER_HOUR
