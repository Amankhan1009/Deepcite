import uuid
from unittest.mock import Mock

import pytest

from app.infrastructure.agents.nodes.approval_gate import approval_gate
from app.infrastructure.agents.state import GraphState


async def test_approval_gate_accepts_true_decision(monkeypatch):
    interrupt_mock = Mock(return_value=True)

    monkeypatch.setattr(
        "app.infrastructure.agents.nodes.approval_gate.interrupt",
        interrupt_mock,
    )

    state: GraphState = {
        "research_run_id": str(uuid.uuid4()),
        "question": "What are production AI risks?",
        "plan": None,
        "sources": [],
        "verified_sources": [],
        "evidence": [],
        "reasoning": {"items": ["Monitoring is required."]},
        "fact_checks": {
            "items": [
                {
                    "claim_index": 0,
                    "status": "supported",
                }
            ]
        },
        "report": None,
    }

    result = await approval_gate(state)

    assert result == {}


async def test_approval_gate_rejects_non_true_decision(monkeypatch):
    def fake_interrupt(_payload):
        return False

    monkeypatch.setattr(
        "app.infrastructure.agents.nodes.approval_gate.interrupt",
        fake_interrupt,
    )

    state = {
        "research_run_id": "test-run-id",
    }

    with pytest.raises(ValueError):
        await approval_gate(state)