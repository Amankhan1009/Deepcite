"""
Milestone 1 spike: does the direct google-genai SDK give us clean
structured output AND tool/function calling in the same shape LangGraph
will expect later (M6 Planning Agent, M7 Research Agent)?

Run standalone, no FastAPI app involved:
    python scripts/gemini_spike.py

Reads GEMINI_API_KEY from the environment. Prints two results:
  1. Structured output — does it return valid, schema-conforming JSON?
  2. Tool calling — does it correctly decide to call a tool and pass
     well-formed arguments?

Read the printed output and report back — that's what settles the SDK
decision in DECISIONS.md.
"""

import json
import os

from google import genai
from google.genai import types
from pydantic import BaseModel


class ResearchPlan(BaseModel):
    sub_questions: list[str]
    strategy: str


def test_structured_output(client: genai.Client) -> None:
    print("\n=== TEST 1: Structured output ===")
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=(
            "Break this research question into 3 sub-questions and a "
            "one-sentence strategy: 'What are the risks of AI agents "
            "operating with persistent memory?'"
        ),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ResearchPlan,
        ),
    )
    print("Raw text:", response.text)
    try:
        parsed = ResearchPlan.model_validate_json(response.text)
        print("Parsed OK:", parsed.model_dump())
    except Exception as e:
        print("FAILED to parse into ResearchPlan:", e)


def test_tool_calling(client: genai.Client) -> None:
    print("\n=== TEST 2: Tool calling ===")

    search_tool = types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="web_search",
                description="Search the web for a query and return results.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={"query": types.Schema(type="STRING")},
                    required=["query"],
                ),
            )
        ]
    )

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents="Find recent sources about LangGraph checkpointing.",
        config=types.GenerateContentConfig(tools=[search_tool]),
    )

    call = None
    for part in response.candidates[0].content.parts:
        if part.function_call:
            call = part.function_call
            break

    if call is None:
        print("FAILED: model did not produce a function call")
        return

    print("Tool called:", call.name)
    print("Arguments:", json.dumps(dict(call.args), indent=2))


def main() -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("Set GEMINI_API_KEY in your environment first.")

    client = genai.Client(api_key=api_key)
    test_structured_output(client)
    test_tool_calling(client)


if __name__ == "__main__":
    main()