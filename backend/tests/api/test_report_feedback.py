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
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    )


async def test_owned_user_can_submit_report_feedback():
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
                    select(User).where(User.email == email),
                )
            ).scalar_one()

            workspace = Workspace(
                user_id=user.id,
                name="Feedback API Test",
            )
            session.add(workspace)
            await session.flush()

            research_run = ResearchRun(
                workspace_id=workspace.id,
                user_id=user.id,
                question="What are the risks of AI deployment?",
                status="completed",
            )
            session.add(research_run)
            await session.flush()

            report = Report(
                research_run_id=research_run.id,
                content_markdown="# AI risks",
            )
            session.add(report)
            await session.commit()

            report_id = report.id
            research_run_id = research_run.id
            workspace_id = workspace.id
            user_id = user.id

        response = await client.post(
            f"/api/v1/reports/{report_id}/feedback",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "decision": "approved",
                "comment": "Useful report",
                "rating": 5,
            },
        )

        assert response.status_code == 201
        assert response.json()["report_id"] == str(report_id)
        assert response.json()["decision"] == "approved"
        assert response.json()["rating"] == 5

        async with AsyncSessionLocal() as session:
            await session.execute(
                delete(Report).where(Report.id == report_id)
            )
            await session.execute(
                delete(ResearchRun).where(
                    ResearchRun.id == research_run_id
                )
            )
            await session.execute(
                delete(Workspace).where(Workspace.id == workspace_id)
            )
            await session.execute(
                delete(User).where(User.id == user_id)
            )
            await session.commit()


async def test_feedback_requires_at_least_one_value():
    async with await _client() as client:
        response = await client.post(
            f"/api/v1/reports/{uuid.uuid4()}/feedback",
            json={},
        )

        assert response.status_code == 401