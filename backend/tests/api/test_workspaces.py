import uuid

from httpx import ASGITransport, AsyncClient

from app.main import app


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _register_and_get_token(client) -> str:
    email = f"{uuid.uuid4()}@example.com"
    resp = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": "testpass123"}
    )
    return resp.json()["access_token"]


async def test_create_list_get_workspace():
    async with await _client() as client:
        token = await _register_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        create_resp = await client.post(
            "/api/v1/workspaces",
            json={"name": "My Research", "description": "test workspace"},
            headers=headers,
        )
        assert create_resp.status_code == 201
        workspace_id = create_resp.json()["id"]

        list_resp = await client.get("/api/v1/workspaces", headers=headers)
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1

        get_resp = await client.get(f"/api/v1/workspaces/{workspace_id}", headers=headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "My Research"


async def test_cannot_access_other_users_workspace():
    async with await _client() as client:
        token_a = await _register_and_get_token(client)
        token_b = await _register_and_get_token(client)

        create_resp = await client.post(
            "/api/v1/workspaces",
            json={"name": "User A's workspace"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        workspace_id = create_resp.json()["id"]

        get_resp = await client.get(
            f"/api/v1/workspaces/{workspace_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert get_resp.status_code == 404


async def test_delete_workspace_removes_it_from_list():
    async with await _client() as client:
        token = await _register_and_get_token(client)
        headers = {"Authorization": f"Bearer {token}"}

        create_resp = await client.post(
            "/api/v1/workspaces", json={"name": "Temp"}, headers=headers
        )
        workspace_id = create_resp.json()["id"]

        delete_resp = await client.delete(f"/api/v1/workspaces/{workspace_id}", headers=headers)
        assert delete_resp.status_code == 204

        list_resp = await client.get("/api/v1/workspaces", headers=headers)
        assert list_resp.json() == []