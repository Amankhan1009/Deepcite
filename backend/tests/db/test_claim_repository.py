import uuid

from sqlalchemy import delete

from app.infrastructure.db.models.claim import Claim
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.repositories.claim_repository import ClaimRepository
from app.infrastructure.db.session import AsyncSessionLocal


async def test_claim_repository_create_and_list():
    async with AsyncSessionLocal() as session:
        user = User(
            email=f"{uuid.uuid4()}@example.com",
            hashed_password="test-hash",
        )
        session.add(user)
        await session.flush()

        workspace = Workspace(
            user_id=user.id,
            name="Claim Repository Test",
        )
        session.add(workspace)
        await session.flush()

        research_run = ResearchRun(
            workspace_id=workspace.id,
            user_id=user.id,
            question="What are the risks of AI systems?",
            status="reasoning",
        )
        session.add(research_run)
        await session.flush()

        repository = ClaimRepository(session)

        claim = await repository.create(
            research_run_id=research_run.id,
            text="Production AI systems require monitoring.",
            supporting_evidence_ids=[str(uuid.uuid4())],
            contradicting_evidence_ids=[],
        )

        claims = await repository.list_for_research_run(research_run.id)

        assert len(claims) == 1
        assert claims[0].id == claim.id
        assert claims[0].text.startswith("Production AI systems")
        assert claims[0].fact_check_status == "unverified"
        assert len(claims[0].supporting_evidence_ids) == 1
        assert claims[0].contradicting_evidence_ids == []

        await session.execute(
            delete(Claim).where(Claim.research_run_id == research_run.id)
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


async def test_claim_repository_returns_empty_for_unknown_run():
    async with AsyncSessionLocal() as session:
        repository = ClaimRepository(session)

        claims = await repository.list_for_research_run(uuid.uuid4())

        assert claims == []