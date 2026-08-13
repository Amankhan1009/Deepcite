"""Milestone 12 provider spike for Groq.

Run from the repository root:

    python scripts/groq_spike.py

The script tests:
1. JSON-schema structured output parsed into the existing ResearchPlan shape.
2. Tool/function calling with well-formed arguments.

Set GROQ_API_KEY in the environment before running.
"""

import json
import os

from groq import Groq
from pydantic import BaseModel


MODEL = "openai/gpt-oss-120b"

RESEARCH_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "sub_questions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "strategy": {"type": "string"},
    },
    "required": ["sub_questions", "strategy"],
    "additionalProperties": False,
}


class ResearchPlan(BaseModel):
    sub_questions: list[str]
    strategy: str


def test_structured_output(client: Groq) -> None:
    print("\n=== TEST 1: Structured output ===")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    "Break this research question into exactly 3 focused "
                    "sub-questions and a one-sentence strategy: What are the "
                    "risks of AI agents operating with persistent memory?"
                ),
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "research_plan",
                "strict": True,
                "schema": RESEARCH_PLAN_SCHEMA,
            },
        },
    )

    raw_text = response.choices[0].message.content or ""
    print("Raw text:", raw_text)

    try:
        parsed = ResearchPlan.model_validate_json(raw_text)
        print("Parsed OK:", parsed.model_dump())
    except Exception as error:
        print("FAILED to parse into ResearchPlan:", error)


def test_tool_calling(client: Groq) -> None:
    print("\n=== TEST 2: Tool calling ===")

    tools = [
        {
            "type": "function",
            "function": {
                "name": "web_search",
                "description": "Search the web for a query and return results.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The web search query.",
                        }
                    },
                    "required": ["query"],
                },
            },
        }
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": "Find recent sources about LangGraph checkpointing.",
            }
        ],
        tools=tools,
        tool_choice="required",
    )

    tool_calls = response.choices[0].message.tool_calls or []

    if not tool_calls:
        print("FAILED: model did not produce a function call")
        return

    tool_call = tool_calls[0]
    print("Tool called:", tool_call.function.name)
    print(
        "Arguments:",
        json.dumps(json.loads(tool_call.function.arguments), indent=2),
    )


def main() -> None:
    api_key = os.environ.get("GROQ_API_KEY")

    if not api_key:
        raise SystemExit("Set GROQ_API_KEY in the environment first.")

    client = Groq(api_key=api_key)
    test_structured_output(client)
    test_tool_calling(client)


if __name__ == "__main__":
    main()
