from langgraph.types import Send

from app.infrastructure.agents.graph import fan_out_research
from app.infrastructure.agents.state import GraphState


def test_fan_out_research_creates_one_task_per_subquestion():
    state: GraphState = {
        "research_run_id": "parallel-test",
        "question": "What are the risks of production AI systems?",
        "plan": {
            "sub_questions": [
                "What are the security risks?",
                "What are the privacy risks?",
                "What are the operational risks?",
            ],
            "strategy": "Search security, privacy, and operations sources.",
        },
        "sources": [],
        "evidence": None,
        "report": None,
    }

    sends = fan_out_research(state)

    assert len(sends) == 3
    assert all(isinstance(item, Send) for item in sends)

    assert sends[0].node == "research_agent"
    assert sends[0].arg == {
        "sub_question": "What are the security risks?",
        "sub_question_index": 0,
    }

    assert sends[1].arg["sub_question_index"] == 1
    assert sends[2].arg["sub_question_index"] == 2


def test_fan_out_research_returns_no_tasks_without_plan():
    state: GraphState = {
        "research_run_id": "empty-plan-test",
        "question": "An unanswered question",
        "plan": None,
        "sources": [],
        "evidence": None,
        "report": None,
    }

    sends = fan_out_research(state)

    assert sends == []