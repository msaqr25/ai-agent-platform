from __future__ import annotations

from fastapi import status
from httpx import AsyncClient


async def test_create_agent(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/agents/", json={"name": "Test Agent", "prompt": "You are a helpful assistant."}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Test Agent"
    assert "id" in data


async def test_create_agent_missing_fields(client: AsyncClient) -> None:
    response = await client.post("/api/v1/agents/", json={})
    assert response.status_code == 422  # noqa: PLR2004


async def test_list_agents(client: AsyncClient) -> None:
    await client.post("/api/v1/agents/", json={"name": "Agent 1"})
    await client.post("/api/v1/agents/", json={"name": "Agent 2"})
    response = await client.get("/api/v1/agents/")
    assert response.status_code == status.HTTP_200_OK
    agents = response.json()
    assert len(agents) == 2  # noqa: PLR2004


async def test_get_agent(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/agents/", json={"name": "Test Agent"})
    agent_id = create_resp.json()["id"]
    response = await client.get(f"/api/v1/agents/{agent_id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == agent_id


async def test_get_agent_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/agents/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_update_agent(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/agents/", json={"name": "Original Name"})
    agent_id = create_resp.json()["id"]
    response = await client.put(f"/api/v1/agents/{agent_id}", json={"name": "Updated Name"})
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == "Updated Name"


async def test_create_agent_extra_fields(client: AsyncClient) -> None:
    response = await client.post("/api/v1/agents/", json={"name": "Agent", "prompt": "Hi", "unknown_field": "oops"})
    assert response.status_code == 422  # noqa: PLR2004


async def test_create_agent_empty_name(client: AsyncClient) -> None:
    response = await client.post("/api/v1/agents/", json={"name": ""})
    assert response.status_code == 422  # noqa: PLR2004
