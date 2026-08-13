from app.infrastructure.agents.state import GraphState


async def supervisor_agent(state: GraphState) -> dict:
    """Decides what runs next based on graph state. Still a single path
    for M6 — becomes real branching once M7+ add agents to choose
    between."""
    return {}


def route_from_supervisor(state: GraphState) -> str:
    return "planning_agent"