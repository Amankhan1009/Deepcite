"""MCP client wrapper around the tavily-mcp server.
Spawns tavily-mcp (official package, tavily-ai/tavily-mcp) as a stdio
subprocess via npx, and exposes a single clean async function for the
Research Agent to call. All MCP protocol details (session handshake,
tool-call framing) are hidden here — the agent node never touches the
MCP SDK directly. See ARCHITECTURE.md §4.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.core.config import get_settings
from app.infrastructure.observability.tracing import traceable_span


@dataclass
class SearchResult:
    url: str
    title: str
    content: str

@traceable_span(
    name="mcp.tavily_search",
    run_type="tool",
)

async def search(query: str, max_results: int = 5) -> list[SearchResult]:
    """Run a web search via the tavily-mcp server's tavily_search tool.

    Spawns a fresh tavily-mcp subprocess per call. Fine for M7's
    single-sub-question scope; M10 (parallel research) may need a
    longer-lived session — revisit then rather than optimizing now.
    """
    settings = get_settings()

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "tavily-mcp@latest"],
        env={**os.environ, "TAVILY_API_KEY": settings.tavily_api_key},
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            result = await session.call_tool(
                "tavily_search",
                arguments={"query": query, "max_results": max_results},
            )

            return _parse_search_results(result)


def _parse_search_results(result) -> list[SearchResult]:
    """tavily_search returns a single text block formatted as repeated
    'Title: ...\\nURL: ...\\nContent: ...' entries — not JSON, despite
    what Tavily's docs imply. Parsed via regex against the real format,
    confirmed against a live call rather than assumed."""
    if not result.content:
        return []

    text_block = result.content[0]
    if text_block.type != "text":
        return []

    pattern = re.compile(
        r"Title:\s*(.*?)\s*\nURL:\s*(.*?)\s*\nContent:\s*(.*?)(?=\nTitle:\s|\Z)",
        re.DOTALL,
    )

    return [
        SearchResult(url=url.strip(), title=title.strip(), content=content.strip())
        for title, url, content in pattern.findall(text_block.text)
    ]
