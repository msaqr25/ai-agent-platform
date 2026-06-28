from __future__ import annotations

from fastapi import status
from httpx import AsyncClient

from tests.conftest import create_agent


async def test_create_session(client: AsyncClient) -> None:
    agent_id = await create_agent(client)
    response = await client.post("/api/v1/sessions/", json={"agent_id": agent_id})
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["agent_id"] == agent_id
    assert "id" in data


async def test_create_session_invalid_agent(client: AsyncClient) -> None:
    response = await client.post("/api/v1/sessions/", json={"agent_id": 9999})
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_session(client: AsyncClient) -> None:
    agent_id = await create_agent(client)
    create_resp = await client.post("/api/v1/sessions/", json={"agent_id": agent_id})
    session_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == session_id


async def test_get_session_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/sessions/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_session(client: AsyncClient) -> None:
    agent_id = await create_agent(client)
    create_resp = await client.post("/api/v1/sessions/", json={"agent_id": agent_id})
    session_id = create_resp.json()["id"]
    response = await client.delete(f"/api/v1/sessions/{session_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    get_resp = await client.get(f"/api/v1/sessions/{session_id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_session_not_found(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/sessions/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_list_sessions_for_agent(client: AsyncClient) -> None:
    agent_id = await create_agent(client)
    await client.post("/api/v1/sessions/", json={"agent_id": agent_id})
    await client.post("/api/v1/sessions/", json={"agent_id": agent_id})
    response = await client.get(f"/api/v1/sessions/agent/{agent_id}")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body["items"]) == 2  # noqa: PLR2004
    assert body["total"] == 2  # noqa: PLR2004


async def test_list_sessions_for_agent_pagination(client: AsyncClient) -> None:
    agent_id = await create_agent(client)
    for _ in range(3):
        await client.post("/api/v1/sessions/", json={"agent_id": agent_id})
    response = await client.get(f"/api/v1/sessions/agent/{agent_id}?skip=0&limit=2")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert len(body["items"]) == 2  # noqa: PLR2004
    assert body["total"] == 3  # noqa: PLR2004


async def test_list_sessions_empty(client: AsyncClient) -> None:
    agent_id = await create_agent(client)
    response = await client.get(f"/api/v1/sessions/agent/{agent_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"items": [], "total": 0}


async def test_create_session_extra_fields(client: AsyncClient) -> None:
    agent_id = await create_agent(client)
    response = await client.post("/api/v1/sessions/", json={"agent_id": agent_id, "extra": "bad"})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_create_session_agent_id_zero(client: AsyncClient) -> None:
    response = await client.post("/api/v1/sessions/", json={"agent_id": 0})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
