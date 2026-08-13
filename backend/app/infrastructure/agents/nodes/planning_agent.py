from app.infrastructure.agents.state import GraphState
from app.infrastructure.llm.groq_client import generate_research_plan


async def planning_agent(state: GraphState) -> dict:
    plan = await generate_research_plan(state["question"])
    return {"plan": plan.model_dump()}
