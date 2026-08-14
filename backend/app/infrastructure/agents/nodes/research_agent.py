import asyncio

from app.infrastructure.agents.state import ResearchTask
from app.infrastructure.mcp.registry import get_search_client

SEARCH_RESULTS_PER_SUBQUESTION = 2

# ============================================================
# MCP SEARCH CONCURRENCY
# ============================================================

_search_semaphore = asyncio.Semaphore(1)


# ============================================================
# RESEARCH AGENT
# ============================================================

async def research_agent(state: ResearchTask) -> dict:
    """Search one planned sub-question through the MCP search client."""

    search_client = get_search_client()

    async with _search_semaphore:
        results = await search_client(
            state["sub_question"],
            SEARCH_RESULTS_PER_SUBQUESTION,
        )

    sub_question_index = state["sub_question_index"]

    return {
        "sources": [
            {
                "source_index": (
                    sub_question_index * SEARCH_RESULTS_PER_SUBQUESTION + index
                ),
                "sub_question_index": sub_question_index,
                "sub_question": state["sub_question"],
                "url": result.url,
                "title": result.title,
                "content": result.content,
            }
            for index, result in enumerate(results)
        ]
    }