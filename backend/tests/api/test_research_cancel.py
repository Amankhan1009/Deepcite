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


async def _register(client) -> tuple[str, str]:
    email = f"{uuid.uuid4()}@example.com"

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "testpass123",
        },
    )

    return response.json()["access_token"], email


async def _create_workspace_and_run(
    *,
    owner_email: str,
    status: str,
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    async with AsyncSessionLocal() as session:
        owner = (
            await session.execute(
                select(User).where(User.email == owner_email)
            )
        ).scalar_one()

        workspace = Workspace(
            user_id=owner.id,
            name=f"Cancel test workspace {uuid.uuid4()}",
        )
        session.add(workspace)
        await session.flush()

        research_run = ResearchRun(
            workspace_id=workspace.id,
            user_id=owner.id,
            question="What are enterprise AI reliability risks?",
            status=status,
        )
        session.add(research_run)
        await session.commit()

        return research_run.id, workspace.id, owner.id


async def _cleanup(
    *,
    run_id: uuid.UUID,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(ResearchRun).where(ResearchRun.id == run_id)
        )
        await session.execute(
            delete(Workspace).where(Workspace.id == workspace_id)
        )
        await session.execute(delete(User).where(User.id == user_id))
        await session.commit()


async def test_owner_can_cancel_researching_run():
    async with await _client() as client:
        token, email = await _register(client)
        run_id, workspace_id, user_id = await _create_workspace_and_run(
            owner_email=email,
            status="researching",
        )

        response = await client.post(
            f"/api/v1/research/{run_id}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

        async with AsyncSessionLocal() as session:
            persisted = await session.get(ResearchRun, run_id)
            assert persisted is not None
            assert persisted.status == "cancelled"

        await _cleanup(
            run_id=run_id,
            workspace_id=workspace_id,
            user_id=user_id,
        )


async def test_owner_can_cancel_awaiting_approval_run():
    async with await _client() as client:
        token, email = await _register(client)
        run_id, workspace_id, user_id = await _create_workspace_and_run(
            owner_email=email,
            status="awaiting_approval",
        )

        response = await client.post(
            f"/api/v1/research/{run_id}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

        await _cleanup(
            run_id=run_id,
            workspace_id=workspace_id,
            user_id=user_id,
        )


async def test_owner_can_cancel_generating_report_run():
    async with await _client() as client:
        token, email = await _register(client)
        run_id, workspace_id, user_id = await _create_workspace_and_run(
            owner_email=email,
            status="generating_report",
        )

        response = await client.post(
            f"/api/v1/research/{run_id}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

        await _cleanup(
            run_id=run_id,
            workspace_id=workspace_id,
            user_id=user_id,
        )


async def test_completed_run_is_not_cancellable():
    async with await _client() as client:
        token, email = await _register(client)
        run_id, workspace_id, user_id = await _create_workspace_and_run(
            owner_email=email,
            status="completed",
        )

        response = await client.post(
            f"/api/v1/research/{run_id}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 409

        await _cleanup(
            run_id=run_id,
            workspace_id=workspace_id,
            user_id=user_id,
        )


async def test_cancelled_run_cannot_be_approved_or_resumed():
    async with await _client() as client:
        token, email = await _register(client)
        run_id, workspace_id, user_id = await _create_workspace_and_run(
            owner_email=email,
            status="cancelled",
        )

        approve_response = await client.post(
            f"/api/v1/research/{run_id}/approve",
            headers={"Authorization": f"Bearer {token}"},
        )
        resume_response = await client.post(
            f"/api/v1/research/{run_id}/resume",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert approve_response.status_code == 409
        assert resume_response.status_code == 409

        await _cleanup(
            run_id=run_id,
            workspace_id=workspace_id,
            user_id=user_id,
        )
