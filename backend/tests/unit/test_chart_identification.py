import os

import pytest

from app.core.config import get_settings
from app.infrastructure.llm.groq_client import identify_chartable_data

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not get_settings().groq_api_key
        or os.getenv("RUN_GROQ_INTEGRATION") != "1",
        reason=(
            "Set GROQ_API_KEY and RUN_GROQ_INTEGRATION=1 "
            "to run chart-identification tests"
        ),
    ),
]


@pytest.mark.asyncio
async def test_chart_identification_returns_spec_for_numeric_findings():
    spec = await identify_chartable_data(
        [
            {
                "claim_index": 0,
                "claim_text": (
                    "Security incidents affected 80% of systems, "
                    "while reliability incidents affected 45%."
                ),
                "status": "supported",
                "supporting_evidence_indexes": [0],
            }
        ]
    )

    assert spec is not None
    assert spec.chart_type in {"bar", "line", "table"}
    assert spec.labels
    assert spec.values
    assert len(spec.labels) == len(spec.values)


@pytest.mark.asyncio
async def test_chart_identification_returns_none_for_qualitative_findings():
    spec = await identify_chartable_data(
        [
            {
                "claim_index": 0,
                "claim_text": (
                    "Production AI systems require careful monitoring "
                    "and governance."
                ),
                "status": "supported",
                "supporting_evidence_indexes": [0],
            }
        ]
    )

    assert spec is None