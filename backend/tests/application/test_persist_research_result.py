import uuid

from sqlalchemy import delete, select

from app.application.use_cases.persist_research_result import (
    persist_report_result,
)
from app.infrastructure.db.models.report import Report
from app.infrastructure.db.models.report_asset import ReportAsset
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.session import AsyncSessionLocal
from app.infrastructure.llm.groq_client import ChartSpec
from app.infrastructure.visualization.chart_generator import render_chart


async def test_persist_report_result_persists_rendered_chart_asset(tmp_path):
    chart_path = tmp_path / "chart.png"

    chart_spec = ChartSpec(
        chart_type="bar",
        title="Security vs Reliability Incidents",
        labels=["Security incidents", "Reliability incidents"],
        values=[80.0, 45.0],
        source_claim_ids=[0],
    )

    rendered_path = render_chart(
        spec=chart_spec,
        output_path=chart_path,
    )

    assert rendered_path.exists()
    assert rendered_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"

    async with AsyncSessionLocal() as session:
        user = User(
            email=f"{uuid.uuid4()}@example.com",
            hashed_password="test-hash",
        )
        session.add(user)
        await session.flush()

        workspace = Workspace(
            user_id=user.id,
            name="Chart Persistence Test",
        )
        session.add(workspace)
        await session.flush()

        research_run = ResearchRun(
            workspace_id=workspace.id,
            user_id=user.id,
            question="Compare security and reliability incidents.",
            status="completed",
        )
        session.add(research_run)
        await session.flush()

        result = {
            "report": {
                "content_markdown": (
                    "# Incident Comparison\n\n"
                    "Security incidents affected 80% of systems "
                    "[Source 1]."
                ),
                "executive_summary": (
                    "Security incidents affected 80% of systems "
                    "[Source 1]."
                ),
            },
            "chart_asset": {
                "asset_type": "chart",
                "file_path": str(rendered_path),
                "caption": chart_spec.title,
            },
        }

        await persist_report_result(
            db=session,
            run=research_run,
            result=result,
        )

        report = (
            await session.execute(
                select(Report).where(
                    Report.research_run_id == research_run.id,
                )
            )
        ).scalar_one()

        assets = list(
            (
                await session.execute(
                    select(ReportAsset).where(
                        ReportAsset.report_id == report.id,
                    )
                )
            ).scalars()
        )

        assert "![Security vs Reliability Incidents]" in (
            report.content_markdown
        )
        assert len(assets) == 1
        assert assets[0].asset_type == "chart"
        assert assets[0].file_path == str(rendered_path)
        assert assets[0].caption == chart_spec.title

        await session.execute(
            delete(ReportAsset).where(
                ReportAsset.report_id == report.id,
            )
        )
        await session.execute(
            delete(Report).where(
                Report.id == report.id,
            )
        )
        await session.execute(
            delete(ResearchRun).where(
                ResearchRun.id == research_run.id,
            )
        )
        await session.execute(
            delete(Workspace).where(
                Workspace.id == workspace.id,
            )
        )
        await session.execute(
            delete(User).where(
                User.id == user.id,
            )
        )
        await session.commit()


async def test_persist_report_result_creates_citations_for_referenced_markers():
    from app.infrastructure.db.models.citation import Citation
    from app.infrastructure.db.models.claim import Claim
    from app.infrastructure.db.models.source import Source
    from app.infrastructure.db.repositories.citation_repository import CitationRepository

    async with AsyncSessionLocal() as session:
        user = User(
            email=f"{uuid.uuid4()}@example.com",
            hashed_password="test-hash",
        )
        session.add(user)
        await session.flush()

        workspace = Workspace(
            user_id=user.id,
            name="Citation Test Workspace",
        )
        session.add(workspace)
        await session.flush()

        research_run = ResearchRun(
            workspace_id=workspace.id,
            user_id=user.id,
            question="What is the impact of LLMs?",
            status="completed",
        )
        session.add(research_run)
        await session.flush()

        source = Source(
            research_run_id=research_run.id,
            url="https://arxiv.org/abs/2401.0001",
            title="LLM Impact Study",
            reliability_score=0.95,
        )
        session.add(source)
        await session.flush()

        claim = Claim(
            research_run_id=research_run.id,
            text="LLMs enhance developer productivity.",
            supporting_evidence_ids=[],
            contradicting_evidence_ids=[],
            fact_check_status="supported",
            confidence_score=0.85,
        )
        session.add(claim)
        await session.flush()

        result = {
            "report": {
                "content_markdown": (
                    "# Summary\n\n"
                    "LLMs increase developer productivity by 25% [Source 1]."
                ),
                "executive_summary": "Summary of findings [Source 1].",
            },
            "sources": [
                {
                    "source_index": 0,
                    "url": "https://arxiv.org/abs/2401.0001",
                    "title": "LLM Impact Study",
                }
            ],
            "verified_sources": [
                {
                    "source_index": 0,
                    "url": "https://arxiv.org/abs/2401.0001",
                    "title": "LLM Impact Study",
                    "reliability_score": 0.95,
                }
            ],
        }

        await persist_report_result(
            db=session,
            run=research_run,
            result=result,
        )

        report = (
            await session.execute(
                select(Report).where(Report.research_run_id == research_run.id)
            )
        ).scalar_one()

        citation_repo = CitationRepository(session)
        citations = await citation_repo.list_for_report(report.id)

        assert len(citations) == 1
        assert citations[0].inline_marker == "[Source 1]"
        assert citations[0].source_id == source.id
        assert citations[0].claim_id == claim.id

        await session.execute(delete(Citation).where(Citation.report_id == report.id))
        await session.execute(delete(Report).where(Report.id == report.id))
        await session.execute(delete(Claim).where(Claim.id == claim.id))
        await session.execute(delete(Source).where(Source.id == source.id))
        await session.execute(delete(ResearchRun).where(ResearchRun.id == research_run.id))
        await session.execute(delete(Workspace).where(Workspace.id == workspace.id))
        await session.execute(delete(User).where(User.id == user.id))
        await session.commit()