from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_health_endpoint_returns_200_and_status_field():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200

    body = response.json()

    assert body == {"status": "ok"}