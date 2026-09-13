"""
Lesson 4 - custom tools via @tool.

Mirrors lessons/04_custom_tools.py, same roll_dice scenario for direct
comparison. Two things are notably SIMPLER here than the SDK's custom-tool
path:

  1. No MCP server wrapping needed - @tool is handed straight to
     create_agent's tools=[] list. LangChain's @tool is just a decorator
     that turns a Python function into a BaseTool; there's no equivalent
     of create_sdk_mcp_server() for in-process tools.
  2. No naming-prefix gotcha - lesson 4 of the SDK curriculum discovered
     tools are actually called as "mcp__<server>__<tool>" at runtime, not
     the bare name. Here, the tool is called by its exact Python function
     name, confirmed directly in the tool_call dict below.

In-process state access (call_log, mutated from inside the tool and read
back afterward) works identically to the SDK version - the tool runs in
this same Python process either way.
"""

import random
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

MODEL = "claude-haiku-4-5"
INPUT_RATE = 1.0 / 1_000_000
OUTPUT_RATE = 5.0 / 1_000_000

call_log: list[str] = []  # direct access to this process's own state from inside the tool


@tool
def roll_dice(sides: int) -> str:
    """Roll an n-sided die and return the actual result."""
    result = random.randint(1, sides)
    call_log.append(f"rolled d{sides} -> {result}")
    return f"Rolled a d{sides}: {result}"


def main():
    agent = create_agent(model=MODEL, tools=[roll_dice])
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Roll two 6-sided dice using the roll_dice tool (one call per "
                        "die), then tell me their sum and whether it's even or odd."
                    ),
                }
            ]
        }
    )

    for msg in result["messages"]:
        print(f"[{type(msg).__name__}] {msg.content!r}")

    final = result["messages"][-1]
    usage = final.usage_metadata or {}
    cost = usage.get("input_tokens", 0) * INPUT_RATE + usage.get("output_tokens", 0) * OUTPUT_RATE
    print(f"\n[cost_usd~] {cost:.6f}")
    print(f"[in-process call_log] {call_log}")


if __name__ == "__main__":
    main()
