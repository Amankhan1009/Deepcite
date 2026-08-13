import uuid

from httpx import ASGITransport, AsyncClient

from app.main import app


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def test_register_then_me():
    email = f"{uuid.uuid4()}@example.com"
    async with await _client() as client:
        register_resp = await client.post(
            "/api/v1/auth/register", json={"email": email, "password": "testpass123"}
        )
        assert register_resp.status_code == 201
        token = register_resp.json()["access_token"]

        me_resp = await client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == email


async def test_login_with_wrong_password_fails():
    email = f"{uuid.uuid4()}@example.com"
    async with await _client() as client:
        await client.post(
            "/api/v1/auth/register", json={"email": email, "password": "correctpass"}
        )
        login_resp = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": "wrongpass"}
        )
        assert login_resp.status_code == 401