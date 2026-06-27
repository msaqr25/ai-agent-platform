from __future__ import annotations

from fastapi import status
from httpx import AsyncClient


async def test_create_session(client: AsyncClient) -> None:
    agent_resp = await client.post("/api/v1/agents/", json={"name": "Test Agent"})
    agent_id = agent_resp.json()["id"]
    response = await client.post("/api/v1/sessions/", json={"agent_id": agent_id})
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["agent_id"] == agent_id
    assert "id" in data


async def test_create_session_invalid_agent(client: AsyncClient) -> None:
    response = await client.post("/api/v1/sessions/", json={"agent_id": 9999})
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_list_sessions_for_agent(client: AsyncClient) -> None:
    agent_resp = await client.post("/api/v1/agents/", json={"name": "Test Agent"})
    agent_id = agent_resp.json()["id"]
    await client.post("/api/v1/sessions/", json={"agent_id": agent_id})
    await client.post("/api/v1/sessions/", json={"agent_id": agent_id})
    response = await client.get(f"/api/v1/sessions/agent/{agent_id}")
    assert response.status_code == status.HTTP_200_OK
    sessions = response.json()
    assert len(sessions) == 2  # noqa: PLR2004


async def test_list_sessions_for_agent_pagination(client: AsyncClient) -> None:
    agent_resp = await client.post("/api/v1/agents/", json={"name": "Test Agent"})
    agent_id = agent_resp.json()["id"]
    for _ in range(3):
        await client.post("/api/v1/sessions/", json={"agent_id": agent_id})
    response = await client.get(f"/api/v1/sessions/agent/{agent_id}?skip=0&limit=2")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2  # noqa: PLR2004


async def test_get_session_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/sessions/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
