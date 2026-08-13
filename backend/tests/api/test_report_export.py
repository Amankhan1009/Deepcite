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


async def test_owned_user_can_export_report_in_all_formats():
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
                name="Report Export API Test",
            )
            session.add(workspace)
            await session.flush()

            research_run = ResearchRun(
                workspace_id=workspace.id,
                user_id=user.id,
                question="How does retrieval improve LLM accuracy?",
                status="completed",
            )
            session.add(research_run)
            await session.flush()

            report = Report(
                research_run_id=research_run.id,
                content_markdown=(
                    "# Retrieval-Augmented Generation\n\n"
                    "Retrieval improves factual accuracy."
                ),
                executive_summary=(
                    "Retrieval provides relevant external context."
                ),
            )
            session.add(report)
            await session.commit()

            report_id = report.id
            research_run_id = research_run.id
            workspace_id = workspace.id
            user_id = user.id

        headers = {
            "Authorization": f"Bearer {token}",
        }

        markdown_response = await client.get(
            f"/api/v1/reports/{report_id}/export",
            params={"format": "markdown"},
            headers=headers,
        )
        pdf_response = await client.get(
            f"/api/v1/reports/{report_id}/export",
            params={"format": "pdf"},
            headers=headers,
        )
        docx_response = await client.get(
            f"/api/v1/reports/{report_id}/export",
            params={"format": "docx"},
            headers=headers,
        )

        assert markdown_response.status_code == 200
        assert markdown_response.headers["content-type"].startswith(
            "text/markdown",
        )
        assert b"Retrieval-Augmented Generation" in markdown_response.content

        assert pdf_response.status_code == 200
        assert pdf_response.headers["content-type"] == "application/pdf"
        assert pdf_response.content.startswith(b"%PDF")

        assert docx_response.status_code == 200
        assert (
            docx_response.headers["content-type"]
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        assert docx_response.content.startswith(b"PK")

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
                delete(Workspace).where(
                    Workspace.id == workspace_id
                )
            )
            await session.execute(
                delete(User).where(User.id == user_id)
            )
            await session.commit()


async def test_report_export_requires_authentication():
    async with await _client() as client:
        response = await client.get(
            f"/api/v1/reports/{uuid.uuid4()}/export",
            params={"format": "pdf"},
        )

        assert response.status_code == 401


async def test_report_export_rejects_unknown_format():
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
            f"/api/v1/reports/{uuid.uuid4()}/export",
            params={"format": "zip"},
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        assert response.status_code == 422