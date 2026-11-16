from datetime import timedelta

import httpx

from app.services.business_day import today_business_date
from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

PROJECTS = "/api/projects"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def test_projects_require_a_session(client: httpx.AsyncClient) -> None:
    assert (await client.get(PROJECTS)).status_code == 401
    assert (await client.post(PROJECTS, json={"name": "x"})).status_code == 401


async def test_create_with_only_a_name_defaults_the_start_date_to_today(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)

    response = await client.post(PROJECTS, json={"name": "Write the book"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Write the book"
    assert body["start_date"] == today_business_date().isoformat()
    assert body["created_business_date"] == today_business_date().isoformat()
    assert body["status"] == "active"


async def test_the_name_is_stripped(client: httpx.AsyncClient) -> None:
    await _login(client)

    body = (await client.post(PROJECTS, json={"name": "  Padded  "})).json()

    assert body["name"] == "Padded"


async def test_a_blank_name_is_rejected(client: httpx.AsyncClient) -> None:
    await _login(client)

    response = await client.post(PROJECTS, json={"name": "   "})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_a_name_longer_than_sixty_characters_is_rejected(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)

    response = await client.post(PROJECTS, json={"name": "x" * 61})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_a_past_start_date_is_accepted_without_backdating_counting(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)
    long_ago = (today_business_date() - timedelta(days=90)).isoformat()

    body = (
        await client.post(PROJECTS, json={"name": "Already going", "start_date": long_ago})
    ).json()

    assert body["start_date"] == long_ago
    # Counting still begins when the project was created, so no backlog of
    # ninety missed days appears (R3).
    assert body["created_business_date"] == today_business_date().isoformat()


async def test_a_future_start_date_is_accepted(client: httpx.AsyncClient) -> None:
    await _login(client)
    tomorrow = (today_business_date() + timedelta(days=1)).isoformat()

    response = await client.post(PROJECTS, json={"name": "Starts tomorrow", "start_date": tomorrow})

    assert response.status_code == 201
    assert response.json()["start_date"] == tomorrow


async def test_the_list_returns_created_projects_in_creation_order(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)
    for name in ("First", "Second", "Third"):
        assert (await client.post(PROJECTS, json={"name": name})).status_code == 201

    body = (await client.get(PROJECTS)).json()

    assert [project["name"] for project in body] == ["First", "Second", "Third"]
    assert [project["sort_order"] for project in body] == sorted(
        project["sort_order"] for project in body
    )


async def test_the_list_is_empty_before_anything_is_created(client: httpx.AsyncClient) -> None:
    await _login(client)

    assert (await client.get(PROJECTS)).json() == []


async def test_an_invalid_date_is_rejected(client: httpx.AsyncClient) -> None:
    await _login(client)

    response = await client.post(PROJECTS, json={"name": "Bad date", "start_date": "2026-02-30"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def _create(client: httpx.AsyncClient, name: str) -> str:
    response = await client.post(PROJECTS, json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


async def test_the_detail_endpoint_returns_one_project(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _create(client, "Detail me")

    response = await client.get(f"{PROJECTS}/{project_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Detail me"


async def test_an_unknown_project_is_a_404_with_a_stable_code(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)

    response = await client.get(f"{PROJECTS}/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "PROJECT_NOT_FOUND"


async def test_renaming_is_visible_in_the_list(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _create(client, "Old name")

    assert (
        await client.patch(f"{PROJECTS}/{project_id}", json={"name": "New name"})
    ).status_code == 200

    listed = (await client.get(PROJECTS)).json()
    assert [project["name"] for project in listed] == ["New name"]


async def test_a_rename_to_blank_is_rejected(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _create(client, "Keep me")

    response = await client.patch(f"{PROJECTS}/{project_id}", json={"name": "   "})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_the_start_date_cannot_be_edited_in_place(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _create(client, "Fixed start")

    response = await client.patch(f"{PROJECTS}/{project_id}", json={"start_date": "2026-01-01"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_the_status_cannot_be_edited_in_place(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _create(client, "Fixed status")

    response = await client.patch(f"{PROJECTS}/{project_id}", json={"status": "paused"})

    assert response.status_code == 422


async def test_sort_order_is_persisted_and_reorders_the_list(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)
    first = await _create(client, "First")
    second = await _create(client, "Second")

    a = (await client.get(f"{PROJECTS}/{first}")).json()["sort_order"]
    b = (await client.get(f"{PROJECTS}/{second}")).json()["sort_order"]
    await client.patch(f"{PROJECTS}/{first}", json={"sort_order": b})
    await client.patch(f"{PROJECTS}/{second}", json={"sort_order": a})

    names = [project["name"] for project in (await client.get(PROJECTS)).json()]
    assert names == ["Second", "First"]


async def test_editing_requires_a_session(client: httpx.AsyncClient) -> None:
    response = await client.patch(
        f"{PROJECTS}/00000000-0000-0000-0000-000000000000", json={"name": "x"}
    )

    assert response.status_code == 401
