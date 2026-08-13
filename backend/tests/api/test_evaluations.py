import uuid
from decimal import Decimal

from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.infrastructure.db.models.evaluation import Evaluation
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.models.user import User
from app.infrastructure.db.models.workspace import Workspace
from app.infrastructure.db.session import AsyncSessionLocal
from app.main import app


async def _client():
    transport = ASGITransport(app=app)
    return AsyncClient(
        transport=transport,
        base_url="http://test",
    )


async def _register(client: AsyncClient) -> tuple[str, str]:
    email = f"{uuid.uuid4()}@example.com"

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "testpass123",
        },
    )

    return response.json()["access_token"], email


async def test_owner_can_get_research_evaluation():
    async with await _client() as client:
        token, email = await _register(client)

        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(
                    select(User).where(User.email == email),
                )
            ).scalar_one()

            workspace = Workspace(
                user_id=user.id,
                name="Evaluation API Test",
            )
            session.add(workspace)
            await session.flush()

            run = ResearchRun(
                workspace_id=workspace.id,
                user_id=user.id,
                question="What are AI risks?",
                status="completed",
            )
            session.add(run)
            await session.flush()

            session.add_all(
                [
                    Evaluation(
                        research_run_id=run.id,
                        dimension="planning_quality",
                        score=Decimal("0.9000"),
                        details={"rationale": "Focused plan."},
                    ),
                    Evaluation(
                        research_run_id=run.id,
                        dimension="groundedness",
                        score=Decimal("0.8500"),
                        details={"unsupported_statements": []},
                    ),
                ]
            )
            await session.commit()

            run_id = run.id
            workspace_id = workspace.id
            user_id = user.id

        response = await client.get(
            f"/api/v1/research/{run_id}/evaluation",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        body = response.json()

        assert len(body) == 2
        assert body[0]["research_run_id"] == str(run_id)
        assert body[0]["dimension"] == "planning_quality"
        assert body[0]["score"] == "0.9000"

        async with AsyncSessionLocal() as session:
            await session.execute(
                delete(Evaluation).where(
                    Evaluation.research_run_id == run_id,
                )
            )
            await session.execute(
                delete(ResearchRun).where(
                    ResearchRun.id == run_id,
                )
            )
            await session.execute(
                delete(Workspace).where(
                    Workspace.id == workspace_id,
                )
            )
            await session.execute(
                delete(User).where(
                    User.id == user_id,
                )
            )
            await session.commit()


async def test_other_user_cannot_get_research_evaluation():
    async with await _client() as client:
        _, owner_email = await _register(client)
        other_token, _ = await _register(client)

        async with AsyncSessionLocal() as session:
            owner = (
                await session.execute(
                    select(User).where(User.email == owner_email),
                )
            ).scalar_one()

            workspace = Workspace(
                user_id=owner.id,
                name="Private Evaluation API Test",
            )
            session.add(workspace)
            await session.flush()

            run = ResearchRun(
                workspace_id=workspace.id,
                user_id=owner.id,
                question="Private question",
                status="completed",
            )
            session.add(run)
            await session.flush()

            session.add(
                Evaluation(
                    research_run_id=run.id,
                    dimension="overall",
                    score=Decimal("0.8000"),
                    details={},
                )
            )
            await session.commit()

            run_id = run.id
            workspace_id = workspace.id
            owner_id = owner.id

        response = await client.get(
            f"/api/v1/research/{run_id}/evaluation",
            headers={"Authorization": f"Bearer {other_token}"},
        )

        assert response.status_code == 404

        async with AsyncSessionLocal() as session:
            await session.execute(
                delete(Evaluation).where(
                    Evaluation.research_run_id == run_id,
                )
            )
            await session.execute(
                delete(ResearchRun).where(
                    ResearchRun.id == run_id,
                )
            )
            await session.execute(
                delete(Workspace).where(
                    Workspace.id == workspace_id,
                )
            )
            await session.execute(
                delete(User).where(
                    User.id == owner_id,
                )
            )
            await session.commit()


async def test_evaluation_summary_is_aggregated_per_dimension():
    async with await _client() as client:
        token, email = await _register(client)

        async with AsyncSessionLocal() as session:
            user = (
                await session.execute(
                    select(User).where(User.email == email),
                )
            ).scalar_one()

            workspace = Workspace(
                user_id=user.id,
                name="Evaluation Summary API Test",
            )
            session.add(workspace)
            await session.flush()

            first_run = ResearchRun(
                workspace_id=workspace.id,
                user_id=user.id,
                question="First question",
                status="completed",
            )
            second_run = ResearchRun(
                workspace_id=workspace.id,
                user_id=user.id,
                question="Second question",
                status="completed",
            )
            session.add_all([first_run, second_run])
            await session.flush()

            session.add_all(
                [
                    Evaluation(
                        research_run_id=first_run.id,
                        dimension="planning_quality",
                        score=Decimal("0.8000"),
                        details={},
                    ),
                    Evaluation(
                        research_run_id=second_run.id,
                        dimension="planning_quality",
                        score=Decimal("1.0000"),
                        details={},
                    ),
                    Evaluation(
                        research_run_id=first_run.id,
                        dimension="groundedness",
                        score=Decimal("0.9000"),
                        details={},
                    ),
                ]
            )
            await session.commit()

            first_run_id = first_run.id
            second_run_id = second_run.id
            workspace_id = workspace.id
            user_id = user.id

        response = await client.get(
            "/api/v1/evaluation/summary",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200

        dimensions = {
            item["dimension"]: item
            for item in response.json()["dimensions"]
        }

        assert dimensions["planning_quality"] == {
            "dimension": "planning_quality",
            "average_score": "0.9000",
            "run_count": 2,
        }

        assert dimensions["groundedness"] == {
            "dimension": "groundedness",
            "average_score": "0.9000",
            "run_count": 1,
        }

        async with AsyncSessionLocal() as session:
            await session.execute(
                delete(Evaluation).where(
                    Evaluation.research_run_id.in_(
                        [first_run_id, second_run_id],
                    )
                )
            )
            await session.execute(
                delete(ResearchRun).where(
                    ResearchRun.id.in_([first_run_id, second_run_id]),
                )
            )
            await session.execute(
                delete(Workspace).where(
                    Workspace.id == workspace_id,
                )
            )
            await session.execute(
                delete(User).where(
                    User.id == user_id,
                )
            )
            await session.commit()
