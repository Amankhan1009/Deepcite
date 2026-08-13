import uuid

from sqlalchemy import delete

from app.infrastructure.db.models.evidence import Evidence
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.models.source import Source
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.repositories.evidence_repository import (
    EvidenceRepository,
)
from app.infrastructure.db.session import AsyncSessionLocal


async def test_evidence_repository_create_and_list():
    async with AsyncSessionLocal() as session:
        user = User(
            email=f"{uuid.uuid4()}@example.com",
            hashed_password="test-hash",
        )
        session.add(user)
        await session.flush()

        workspace = Workspace(
            user_id=user.id,
            name="Evidence Repository Test",
        )
        session.add(workspace)
        await session.flush()

        research_run = ResearchRun(
            workspace_id=workspace.id,
            user_id=user.id,
            question="What are the benefits of MCP?",
            status="researching",
        )
        session.add(research_run)
        await session.flush()

        source = Source(
            research_run_id=research_run.id,
            url="https://example.com/evidence",
            title="Evidence source",
            raw_content_ref="Source content",
        )
        session.add(source)
        await session.flush()

        repository = EvidenceRepository(session)

        evidence = await repository.create(
            research_run_id=research_run.id,
            source_id=source.id,
            claim_text="MCP standardizes communication between AI applications and tools.",
        )

        results = await repository.list_for_research_run(research_run.id)

        assert len(results) == 1
        assert results[0].id == evidence.id
        assert results[0].source_id == source.id
        assert results[0].claim_text.startswith("MCP standardizes")

        await session.execute(
            delete(Evidence).where(Evidence.research_run_id == research_run.id)
        )
        await session.execute(
            delete(Source).where(Source.research_run_id == research_run.id)
        )
        await session.execute(
            delete(ResearchRun).where(ResearchRun.id == research_run.id)
        )
        await session.execute(
            delete(Workspace).where(Workspace.id == workspace.id)
        )
        await session.execute(
            delete(User).where(User.id == user.id)
        )
        await session.commit()


async def test_evidence_repository_returns_empty_for_unknown_run():
    async with AsyncSessionLocal() as session:
        repository = EvidenceRepository(session)

        results = await repository.list_for_research_run(uuid.uuid4())

        assert results == []