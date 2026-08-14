import uuid

from langgraph.graph import END, StateGraph
from langgraph.types import Command, Send

from app.infrastructure.agents.checkpointer import get_checkpointer
from app.infrastructure.agents.nodes.approval_gate import approval_gate
from app.infrastructure.agents.nodes.evaluation_agent import (
    evaluation_agent,
)
from app.infrastructure.agents.nodes.evidence_agent import evidence_agent
from app.infrastructure.agents.nodes.fact_checking_agent import (
    fact_checking_agent,
)
from app.infrastructure.agents.nodes.planning_agent import planning_agent
from app.infrastructure.agents.nodes.reasoning_agent import reasoning_agent
from app.infrastructure.agents.nodes.report_agent import report_agent
from app.infrastructure.agents.nodes.research_agent import research_agent
from app.infrastructure.agents.nodes.supervisor import (
    route_from_supervisor,
    supervisor_agent,
)
from app.infrastructure.agents.nodes.verification_agent import (
    verification_agent,
)
from app.infrastructure.agents.state import GraphState
from app.infrastructure.db.models.research_run import ResearchRun
from app.infrastructure.db.session import AsyncSessionLocal
from app.infrastructure.observability.tracing import traceable_span


class ResearchRunCancelledError(Exception):
    """Raised when a cancelled run attempts to continue graph execution."""


def fan_out_research(state: GraphState) -> list[Send]:
    """Create one parallel Research Agent task per planned sub-question."""
    plan = state.get("plan") or {}
    sub_questions = plan.get("sub_questions") or []

    return [
        Send(
            "research_agent",
            {
                "research_run_id": state["research_run_id"],
                "sub_question": sub_question,
                "sub_question_index": index,
            },
        )
        for index, sub_question in enumerate(sub_questions)
    ]


def _trace_node(name: str, node):
    return traceable_span(
        name=f"agent.{name}",
        run_type="chain",
    )(node)


async def _research_run_is_cancelled(research_run_id: str) -> bool:
    try:
        run_uuid = uuid.UUID(research_run_id)
    except ValueError:
        return False

    async with AsyncSessionLocal() as db:
        run = await db.get(ResearchRun, run_uuid)

        if run is None:
            return False

        return run.status == "cancelled"


def _node_with_cancellation_guard(name: str, node):
    traced_node = _trace_node(name, node)

    async def guarded_node(state: dict) -> dict:
        research_run_id = state.get("research_run_id")

        if research_run_id and await _research_run_is_cancelled(research_run_id):
            raise ResearchRunCancelledError(
                f"Research run {research_run_id} was cancelled",
            )

        return await traced_node(state)

    return guarded_node


def build_graph() -> StateGraph:
    builder = StateGraph(GraphState)

    builder.add_node(
        "supervisor_agent",
        _node_with_cancellation_guard(
            "supervisor_agent",
            supervisor_agent,
        ),
    )
    builder.add_node(
        "planning_agent",
        _node_with_cancellation_guard(
            "planning_agent",
            planning_agent,
        ),
    )
    builder.add_node(
        "research_agent",
        _node_with_cancellation_guard(
            "research_agent",
            research_agent,
        ),
    )
    builder.add_node(
        "verification_agent",
        _node_with_cancellation_guard(
            "verification_agent",
            verification_agent,
        ),
    )
    builder.add_node(
        "evidence_agent",
        _node_with_cancellation_guard(
            "evidence_agent",
            evidence_agent,
        ),
    )
    builder.add_node(
        "reasoning_agent",
        _node_with_cancellation_guard(
            "reasoning_agent",
            reasoning_agent,
        ),
    )
    builder.add_node(
        "fact_checking_agent",
        _node_with_cancellation_guard(
            "fact_checking_agent",
            fact_checking_agent,
        ),
    )
    builder.add_node(
        "approval_gate",
        _node_with_cancellation_guard(
            "approval_gate",
            approval_gate,
        ),
    )
    builder.add_node(
        "report_agent",
        _node_with_cancellation_guard(
            "report_agent",
            report_agent,
        ),
    )
    builder.add_node(
        "evaluation_agent",
        _node_with_cancellation_guard(
            "evaluation_agent",
            evaluation_agent,
        ),
    )
    builder.set_entry_point("supervisor_agent")

    builder.add_conditional_edges(
        "supervisor_agent",
        traceable_span(
            name="graph.route_from_supervisor",
            run_type="chain",
        )(route_from_supervisor),
        {"planning_agent": "planning_agent"},
    )

    builder.add_conditional_edges(
        "planning_agent",
        traceable_span(
            name="graph.fan_out_research",
            run_type="chain",
        )(fan_out_research),
    )

    builder.add_edge("research_agent", "verification_agent")
    builder.add_edge("verification_agent", "evidence_agent")
    builder.add_edge("evidence_agent", "reasoning_agent")
    builder.add_edge("reasoning_agent", "fact_checking_agent")
    builder.add_edge("fact_checking_agent", "approval_gate")
    builder.add_edge("approval_gate", "report_agent")
    builder.add_edge("report_agent", "evaluation_agent")
    builder.add_edge("evaluation_agent", END)

    return builder


@traceable_span(
    name="research_graph",
    run_type="chain",
)
async def _invoke_graph(
    graph_input: dict | Command | None,
    research_run_id: str,
) -> dict:
    builder = build_graph()

    async with get_checkpointer() as checkpointer:
        graph = builder.compile(checkpointer=checkpointer)

        config = {
            "configurable": {
                "thread_id": research_run_id,
            }
        }

        return await graph.ainvoke(
            graph_input,
            config=config,
        )


async def run_research_graph(
    research_run_id: str,
    question: str,
) -> dict:
    """Start a new research graph execution."""

    initial_state: GraphState = {
        "research_run_id": research_run_id,
        "question": question,
        "plan": None,
        "sources": [],
        "verified_sources": None,
        "evidence": None,
        "reasoning": None,
        "fact_checks": None,
        "chart_asset": None,
        "report": None,
    }

    return await _invoke_graph(
        graph_input=initial_state,
        research_run_id=research_run_id,
    )


async def approve_research_graph(
    research_run_id: str,
) -> dict:
    """Resume the graph after explicit human approval."""

    return await _invoke_graph(
        graph_input=Command(resume=True),
        research_run_id=research_run_id,
    )


async def resume_research_graph(
    research_run_id: str,
) -> dict:
    """Resume graph execution from the latest crash-recovery checkpoint."""

    return await _invoke_graph(
        graph_input=None,
        research_run_id=research_run_id,
    )