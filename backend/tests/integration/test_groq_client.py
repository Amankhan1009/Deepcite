import os

import pytest

from app.core.config import get_settings
from app.infrastructure.llm.groq_client import generate_research_plan

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not get_settings().groq_api_key or os.getenv("RUN_GROQ_INTEGRATION") != "1",
        reason=(
            "Set GROQ_API_KEY and RUN_GROQ_INTEGRATION=1 to run the real Groq test"
        ),
    ),
]


@pytest.mark.asyncio
async def test_groq_client_generates_a_valid_research_plan():
    plan = await generate_research_plan(
        "What are the main operational risks of production AI systems?"
    )

    assert plan.sub_questions
    assert 3 <= len(plan.sub_questions) <= 5
    assert plan.strategy.strip()
