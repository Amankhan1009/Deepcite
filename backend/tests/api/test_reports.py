import uuid

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


async def test_get_owned_report():
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

        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(
                    select(User).where(User.email == email)
                )
            ).scalar_one()

            workspace = Workspace(
                user_id=user.id,
                name="Report API Test",
            )
            session.add(workspace)
            await session.flush()

            research_run = ResearchRun(
                workspace_id=workspace.id,
                user_id=user.id,
                question="What are production AI risks?",
                status="completed",
            )
            session.add(research_run)
            await session.flush()

            report = Report(
                research_run_id=research_run.id,
                content_markdown="# Production AI Risks\n\nFinding [Source 1].",
                executive_summary="Finding [Source 1].",
            )
            session.add(report)
            await session.commit()

            research_run_id = research_run.id

            response = await client.get(
                f"/api/v1/research/{research_run_id}/report",
                headers={"Authorization": f"Bearer {token}"},
            )

            assert response.status_code == 200
            assert response.json()["research_run_id"] == str(research_run_id)
            assert "[Source 1]" in response.json()["content_markdown"]

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
                    Workspace.id == workspace.id
                )
            )
            await session.execute(
                delete(User).where(User.id == user.id)
            )
            await session.commit()


async def test_get_report_requires_authentication():
    async with await _client() as client:
        response = await client.get(
            f"/api/v1/research/{uuid.uuid4()}/report"
        )

        assert response.status_code == 401