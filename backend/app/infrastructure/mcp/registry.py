from collections.abc import Awaitable, Callable

from app.infrastructure.mcp.tavily_client import SearchResult, search

SearchClient = Callable[[str, int], Awaitable[list[SearchResult]]]


def get_search_client() -> SearchClient:
    """Return the configured MCP-backed search client."""
    return search