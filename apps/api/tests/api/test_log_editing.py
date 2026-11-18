import httpx

from tests.conftest import ACCOUNT_EMAIL, ACCOUNT_PASSWORD

LOGS = "/api/logs"
PROJECTS = "/api/projects"
TODAY = "/api/today"


async def _login(client: httpx.AsyncClient) -> None:
    response = await client.post(
        "/api/auth/login", json={"email": ACCOUNT_EMAIL, "password": ACCOUNT_PASSWORD}
    )
    assert response.status_code == 200


async def _project(client: httpx.AsyncClient) -> str:
    return (await client.post(PROJECTS, json={"name": "Write a little"})).json()["id"]


async def _log(client: httpx.AsyncClient, project_id: str, content: str = "first") -> dict:
    response = await client.post(LOGS, json={"project_id": project_id, "content": content})
    assert response.status_code == 201
    return response.json()


async def test_tags_round_trip_on_create(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)

    created = await client.post(
        LOGS,
        json={"project_id": project_id, "content": "x", "tags": [" deep work ", "deep work"]},
    )

    assert created.status_code == 201
    # Trimmed, de-duplicated, order preserved.
    assert created.json()["tags"] == ["deep work"]


async def test_editing_changes_content_duration_and_tags(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    log = await _log(client, project_id)

    response = await client.patch(
        f"{LOGS}/{log['id']}",
        json={"content": "edited", "duration_minutes": 45, "tags": ["writing"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["content"] == "edited"
    assert body["duration_minutes"] == 45
    assert body["tags"] == ["writing"]
    assert body["business_date"] == log["business_date"]


async def test_editing_cannot_move_a_log_to_another_day(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    log = await _log(client, project_id)

    response = await client.patch(f"{LOGS}/{log['id']}", json={"business_date": "2026-01-01"})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_editing_cannot_reassign_a_log_to_another_project(
    client: httpx.AsyncClient,
) -> None:
    await _login(client)
    project_id = await _project(client)
    log = await _log(client, project_id)

    response = await client.patch(
        f"{LOGS}/{log['id']}", json={"project_id": "00000000-0000-0000-0000-000000000000"}
    )

    assert response.status_code == 422


async def test_editing_keeps_the_day_checked_in(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    log = await _log(client, project_id)

    await client.patch(f"{LOGS}/{log['id']}", json={"content": "still here"})

    today = (await client.get(TODAY)).json()["projects"][0]
    assert today["recorded"] is True
    assert today["last_log"]["content"] == "still here"


async def test_blank_content_is_refused_on_edit(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    log = await _log(client, project_id)

    response = await client.patch(f"{LOGS}/{log['id']}", json={"content": "   "})

    assert response.status_code == 422


async def test_editing_an_unknown_log_is_a_404(client: httpx.AsyncClient) -> None:
    await _login(client)

    response = await client.patch(
        f"{LOGS}/00000000-0000-0000-0000-000000000000", json={"content": "x"}
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "LOG_NOT_FOUND"


async def test_the_list_returns_a_projects_logs_newest_first(client: httpx.AsyncClient) -> None:
    await _login(client)
    project_id = await _project(client)
    await _log(client, project_id, "older")
    await _log(client, project_id, "newer")

    body = (await client.get(LOGS, params={"project_id": project_id})).json()

    assert [entry["content"] for entry in body] == ["newer", "older"]


async def test_the_list_can_be_filtered_by_project(client: httpx.AsyncClient) -> None:
    await _login(client)
    first = await _project(client)
    second = (await client.post(PROJECTS, json={"name": "Second"})).json()["id"]
    await _log(client, first, "belongs to first")
    await _log(client, second, "belongs to second")

    body = (await client.get(LOGS, params={"project_id": first})).json()

    assert [entry["content"] for entry in body] == ["belongs to first"]
