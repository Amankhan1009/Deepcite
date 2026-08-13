import uuid

from httpx import ASGITransport, AsyncClient

from app.main import app


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(
        transport=transport,
        base_url="http://test",
    )


async def test_missing_research_status_returns_not_found():
    email = f"{uuid.uuid4()}@example.com"

    async with await _client() as client:
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "testpass123",
            },
        )

        token = register_response.json()["access_token"]

        response = await client.get(
            f"/api/v1/research/{uuid.uuid4()}",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

    assert response.status_code == 404