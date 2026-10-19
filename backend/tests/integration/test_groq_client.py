import os

import pytest

from app.core.config import get_settings
from app.infrastructure.llm.groq_client import (
    generate_evidence,
    generate_fact_checks,
    generate_research_plan,
)

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


@pytest.mark.asyncio
async def test_groq_client_generates_evidence_with_question_context():
    source_content = (
        "In a 2024 trial across 40 hospitals, clinical decision support AI "
        "reduced medication dosing errors by 28%. "
        "However, alert fatigue increased clinician override rates to 42% for "
        "non-critical notifications. "
        "Deepcite software disclaimer: All rights reserved 2025. Terms and Conditions apply."
    )
    result = await generate_evidence(
        source_title="Clinical AI Study",
        source_content=source_content,
        research_question="What are the clinical impacts of AI decision support systems?",
        sub_question="How does AI affect medication errors in hospitals?",
    )
    assert result.items
    assert any("28%" in item or "dosing" in item.lower() for item in result.items)


@pytest.mark.asyncio
async def test_groq_client_generates_fact_checks_with_calibrated_statuses():
    reasoning = [
        {"claim_text": "Clinical AI reduces medication dosing errors by 28% in hospital settings."},
        {"claim_text": "Clinical AI completely eliminates the need for human doctors."},
    ]
    evidence = [
        {
            "source_index": 0,
            "claim_text": (
                "Clinical decision support AI reduced medication dosing errors by 28% "
                "across 40 hospitals."
            ),
        }
    ]
    result = await generate_fact_checks(
        question="What are the clinical impacts of AI decision support systems?",
        reasoning=reasoning,
        evidence=evidence,
    )
    assert result.items
    valid_statuses = {
        "supported",
        "partially_supported",
        "uncertain",
        "unsupported",
        "contradicted",
        "irrelevant",
    }
    for item in result.items:
        assert item.status in valid_statuses

    assert result.items[0].status == "supported"
    assert result.items[1].status in {
        "unsupported",
        "contradicted",
        "uncertain",
        "irrelevant",
    }
