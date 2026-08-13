import uuid

from sqlalchemy import delete

from app.infrastructure.db.models.citation import Citation
from app.infrastructure.db.models.claim import Claim
from app.infrastructure.db.models.report import Report
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.models.source import Source
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.repositories.citation_repository import (
    CitationRepository,
)
from app.infrastructure.db.session import AsyncSessionLocal


async def test_citation_repository_create_and_list():
    async with AsyncSessionLocal() as session:
        user = User(
            email=f"{uuid.uuid4()}@example.com",
            hashed_password="test-hash",
        )
        session.add(user)
        await session.flush()

        workspace = Workspace(
            user_id=user.id,
            name="Citation Repository Test",
        )
        session.add(workspace)
        await session.flush()

        research_run = ResearchRun(
            workspace_id=workspace.id,
            user_id=user.id,
            question="What are the risks of AI systems?",
            status="completed",
        )
        session.add(research_run)
        await session.flush()

        source = Source(
            research_run_id=research_run.id,
            url="https://example.com/ai-risks",
            title="AI Risks",
            reliability_score=0.9,
        )
        session.add(source)
        await session.flush()

        claim = Claim(
            research_run_id=research_run.id,
            text="AI systems require monitoring.",
            supporting_evidence_ids=[],
            contradicting_evidence_ids=[],
            fact_check_status="supported",
            confidence_score=0.85,
        )
        session.add(claim)
        await session.flush()

        report = Report(
            research_run_id=research_run.id,
            content_markdown="AI systems require monitoring [Source 1].",
            executive_summary="AI systems require monitoring [Source 1].",
            overall_confidence_score=0.85,
        )
        session.add(report)
        await session.flush()

        repository = CitationRepository(session)

        citation = await repository.create(
            report_id=report.id,
            claim_id=claim.id,
            source_id=source.id,
            inline_marker="[Source 1]",
        )

        citations = await repository.list_for_report(report.id)

        assert len(citations) == 1
        assert citations[0].id == citation.id
        assert citations[0].report_id == report.id
        assert citations[0].claim_id == claim.id
        assert citations[0].source_id == source.id
        assert citations[0].inline_marker == "[Source 1]"

        await session.execute(
            delete(Citation).where(
                Citation.report_id == report.id,
            )
        )
        await session.execute(
            delete(Report).where(
                Report.id == report.id,
            )
        )
        await session.execute(
            delete(Claim).where(
                Claim.id == claim.id,
            )
        )
        await session.execute(
            delete(Source).where(
                Source.id == source.id,
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


async def test_citation_repository_returns_empty_for_unknown_report():
    async with AsyncSessionLocal() as session:
        repository = CitationRepository(session)

        citations = await repository.list_for_report(uuid.uuid4())

        assert citations == []