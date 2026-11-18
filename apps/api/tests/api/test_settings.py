from datetime import timedelta

import httpx

from app.services.business_day import today_business_date
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

SETTINGS = "/api/settings"
REST_DAYS = "/api/settings/rest-days"
TODAY = "/api/today"
LOGS = "/api/logs"
PROJECTS = "/api/projects"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def test_settings_require_a_session(client: httpx.AsyncClient) -> None:
    assert (await client.get(SETTINGS)).status_code == 401


async def test_the_default_rest_days_are_the_weekend(client: httpx.AsyncClient) -> None:
    await _login(client)

    body = (await client.get(SETTINGS)).json()

    assert body["rest_weekdays"] == [6, 7]
    assert body["effective_from"] is None


async def test_changing_rest_days_is_stored_with_an_effective_date(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)

    updated = await client.put(REST_DAYS, json={"rest_weekdays": [7]})
    read_back = await client.get(SETTINGS)

    assert updated.status_code == 200
    assert updated.json()["rest_weekdays"] == [7]
    assert updated.json()["effective_from"] == today_business_date().isoformat()
    assert read_back.json()["rest_weekdays"] == [7]


async def test_all_seven_rest_days_are_refused(client: httpx.AsyncClient) -> None:
    await _login(client)

    response = await client.put(REST_DAYS, json={"rest_weekdays": [1, 2, 3, 4, 5, 6, 7]})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REST_DAYS_INVALID"


async def test_no_rest_days_is_allowed(client: httpx.AsyncClient) -> None:
    await _login(client)

    response = await client.put(REST_DAYS, json={"rest_weekdays": []})

    assert response.status_code == 200
    assert response.json()["rest_weekdays"] == []


async def test_a_future_effective_date_is_refused(client: httpx.AsyncClient) -> None:
    await _login(client)
    tomorrow = (today_business_date() + timedelta(days=1)).isoformat()

    response = await client.put(REST_DAYS, json={"rest_weekdays": [7], "effective_from": tomorrow})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "BUSINESS_DATE_IN_FUTURE"


async def test_changing_rest_days_twice_in_one_day_updates_the_same_rule(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)

    first = await client.put(REST_DAYS, json={"rest_weekdays": [7]})
    second = await client.put(REST_DAYS, json={"rest_weekdays": [6]})
    read_back = await client.get(SETTINGS)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["rest_weekdays"] == [6]
    assert read_back.json()["rest_weekdays"] == [6]
    assert read_back.json()["effective_from"] == today_business_date().isoformat()


async def test_a_rest_day_stops_being_an_expected_day(client: httpx.AsyncClient) -> None:
    await _login(client)
    today = today_business_date()
    project = (await client.post(PROJECTS, json={"name": "Write a little"})).json()
    await client.post(LOGS, json={"project_id": project["id"], "content": "today"})

    before = (await client.get(TODAY)).json()["projects"][0]
    await client.put(REST_DAYS, json={"rest_weekdays": [today.isoweekday()]})
    after = (await client.get(TODAY)).json()["projects"][0]

    assert before["current_streak"] == 1
    assert before["is_rest_day"] is False
    # Today is now rest, so no expected day remains for a project created
    # today: the record still exists, but it is not a streak day.
    assert after["is_rest_day"] is True
    assert after["recorded"] is True
    assert after["current_streak"] == 0
