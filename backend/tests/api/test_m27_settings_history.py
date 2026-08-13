import uuid

from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.session import AsyncSessionLocal
from app.main import app


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


async def _register(client) -> str:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{uuid.uuid4()}@example.com",
            "password": "testpass123",
        },
    )

    assert response.status_code == 201

    return response.json()["access_token"]


async def test_settings_default_and_update():
    async with await _client() as client:
        token = await _register(client)
        headers = {"Authorization": f"Bearer {token}"}

        default_response = await client.get(
            "/api/v1/settings",
            headers=headers,
        )

        assert default_response.status_code == 200
        assert default_response.json()["display_name"] is None
        assert default_response.json()["timezone"] == "UTC"
        assert default_response.json()["theme"] == "system"

        update_response = await client.patch(
            "/api/v1/settings",
            headers=headers,
            json={
                "display_name": "Deepcite User",
                "timezone": "Asia/Kolkata",
                "theme": "dark",
            },
        )

        assert update_response.status_code == 200
        assert update_response.json()["display_name"] == "Deepcite User"
        assert update_response.json()["timezone"] == "Asia/Kolkata"
        assert update_response.json()["theme"] == "dark"

        persisted_response = await client.get(
            "/api/v1/settings",
            headers=headers,
        )

        assert persisted_response.status_code == 200
        assert persisted_response.json()["display_name"] == "Deepcite User"
        assert persisted_response.json()["timezone"] == "Asia/Kolkata"
        assert persisted_response.json()["theme"] == "dark"


async def test_invalid_theme_is_rejected():
    async with await _client() as client:
        token = await _register(client)

        response = await client.patch(
            "/api/v1/settings",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "display_name": "Invalid Theme User",
                "timezone": "UTC",
                "theme": "blue",
            },
        )

        assert response.status_code == 422


async def test_workspace_research_history_is_returned_newest_first():
    async with await _client() as client:
        email = f"{uuid.uuid4()}@example.com"

        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "testpass123",
            },
        )

        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(
                    select(User).where(User.email == email),
                )
            ).scalar_one()

            workspace = Workspace(
                user_id=user.id,
                name="History Test Workspace",
            )
            session.add(workspace)
            await session.flush()

            first_run = ResearchRun(
                workspace_id=workspace.id,
                user_id=user.id,
                question="First historical research question",
                status="completed",
            )

            second_run = ResearchRun(
                workspace_id=workspace.id,
                user_id=user.id,
                question="Second historical research question",
                status="awaiting_approval",
            )

            session.add_all([first_run, second_run])
            await session.commit()

            workspace_id = workspace.id
            first_run_id = first_run.id
            second_run_id = second_run.id
            user_id = user.id

        response = await client.get(
            f"/api/v1/workspaces/{workspace_id}/research",
            headers=headers,
        )

        assert response.status_code == 200

        history = response.json()

        assert len(history) == 2
        assert {item["id"] for item in history} == {
            str(first_run_id),
            str(second_run_id),
        }
        assert {
            item["question"]
            for item in history
        } == {
            "First historical research question",
            "Second historical research question",
        }

        async with AsyncSessionLocal() as session:
            await session.execute(
                delete(ResearchRun).where(
                    ResearchRun.user_id == user_id,
                )
            )
            await session.execute(
                delete(Workspace).where(
                    Workspace.id == workspace_id,
                )
            )
            await session.execute(
                delete(User).where(
                    User.id == user_id,
                )
            )
            await session.commit()


async def test_workspace_history_is_hidden_from_other_users():
    async with await _client() as client:
        token_a = await _register(client)
        token_b = await _register(client)

        create_response = await client.post(
            "/api/v1/workspaces",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"name": "Private History Workspace"},
        )

        workspace_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/workspaces/{workspace_id}/research",
            headers={"Authorization": f"Bearer {token_b}"},
        )

        assert response.status_code == 200
        assert response.json() == []
        