import uuid
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.infrastructure.db.models.report import Report
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


async def test_owner_can_approve_awaiting_research_run(monkeypatch):
    async with await _client() as client:
        token, email = await _register(client)

        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(
                    select(User).where(User.email == email)
                )
            ).scalar_one()

            workspace = Workspace(
                user_id=user.id,
                name="Approval Test Workspace",
            )
            session.add(workspace)
            await session.flush()

            research_run = ResearchRun(
                workspace_id=workspace.id,
                user_id=user.id,
                question="What are production AI risks?",
                status="awaiting_approval",
            )
            session.add(research_run)
            await session.commit()

            research_run_id = research_run.id
            workspace_id = workspace.id
            user_id = user.id

        monkeypatch.setattr(
            "app.application.use_cases.approve_research_run."
            "approve_research_graph",
            AsyncMock(
                return_value={
                    "report": {
                        "content_markdown": (
                            "# Production AI Risks\n\n"
                            "Monitoring is required."
                        ),
                        "executive_summary": (
                            "Monitoring is required."
                        ),
                    }
                }
            ),
        )

        response = await client.post(
            f"/api/v1/research/{research_run_id}/approve",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        async with AsyncSessionLocal() as session:
            report = (
                await session.execute(
                    select(Report).where(
                        Report.research_run_id == research_run_id
                    )
                )
            ).scalar_one()

            assert "Monitoring is required." in report.content_markdown

            await session.execute(
                delete(Report).where(
                    Report.research_run_id == research_run_id
                )
            )
            await session.execute(
                delete(ResearchRun).where(
                    ResearchRun.id == research_run_id
                )
            )
            await session.execute(
                delete(Workspace).where(
                    Workspace.id == workspace_id
                )
            )
            await session.execute(
                delete(User).where(
                    User.id == user_id
                )
            )
            await session.commit()


async def test_other_user_cannot_approve_research_run():
    async with await _client() as client:
        owner_token, owner_email = await _register(client)
        other_token, _ = await _register(client)

        async with AsyncSessionLocal() as session:
            owner = (
                await session.execute(
                    select(User).where(User.email == owner_email)
                )
            ).scalar_one()

            workspace = Workspace(
                user_id=owner.id,
                name="Private Approval Workspace",
            )
            session.add(workspace)
            await session.flush()

            research_run = ResearchRun(
                workspace_id=workspace.id,
                user_id=owner.id,
                question="Private research question",
                status="awaiting_approval",
            )
            session.add(research_run)
            await session.commit()

            research_run_id = research_run.id
            workspace_id = workspace.id
            owner_id = owner.id

        response = await client.post(
            f"/api/v1/research/{research_run_id}/approve",
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert response.status_code == 404

        async with AsyncSessionLocal() as session:
            await session.execute(
                delete(ResearchRun).where(
                    ResearchRun.id == research_run_id
                )
            )
            await session.execute(
                delete(Workspace).where(
                    Workspace.id == workspace_id
                )
            )
            await session.execute(
                delete(User).where(
                    User.id == owner_id
                )
            )
            await session.commit()