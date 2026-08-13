import uuid

from sqlalchemy import delete

from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.models.source import Source
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.repositories.source_repository import SourceRepository
from app.infrastructure.db.session import AsyncSessionLocal


async def test_source_repository_create_and_list():
    async with AsyncSessionLocal() as session:
        user = User(
            email=f"{uuid.uuid4()}@example.com",
            hashed_password="test-hash",
        )
        session.add(user)
        await session.flush()

        workspace = Workspace(
            user_id=user.id,
            name="Source Repository Test",
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

        repository = SourceRepository(session)

        first_source = await repository.create(
        research_run_id=research_run.id,
        url="https://example.com/one",
        title="First source",
        raw_content_ref="First source content",
        reliability_score=0.85,
        )

        second_source = await repository.create(
            research_run_id=research_run.id,
            url="https://example.com/two",
            title="Second source",
            raw_content_ref="Second source content",
        )

        sources = await repository.list_for_research_run(research_run.id)

        assert len(sources) == 2
        assert sources[0].id == first_source.id
        assert sources[0].url == "https://example.com/one"
        assert sources[1].id == second_source.id
        assert sources[1].url == "https://example.com/two"
        assert sources[0].reliability_score == 0.85

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


async def test_source_repository_returns_empty_list_for_unknown_run():
    async with AsyncSessionLocal() as session:
        repository = SourceRepository(session)

        sources = await repository.list_for_research_run(uuid.uuid4())

        assert sources == []