"""
Lesson 7 - the subagents-as-tools pattern.

Mirrors lessons/07_subagents.py: delegate haiku-writing to a specialist.
LangChain has no separate "subagent" primitive or "Agent" built-in tool -
a subagent is just ANOTHER create_agent(...), wrapped in a plain @tool
function that calls its .invoke() and returns the final message's
content. The parent agent sees it as an ordinary tool with no idea it's
actually a whole other agent underneath.

Notably simpler than the SDK version here: this runs synchronously,
in-process, with none of the background-task machinery (task_started/
task_updated/thinking_tokens system messages) the SDK's Agent tool
produced. No surprises to report this time - it just works exactly as
the pattern describes.
"""

import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

MODEL = "claude-haiku-4-5"

HAIKU_PERSONA = (
    "You are a haiku-writing specialist. When given a topic, respond with "
    "exactly one haiku (5-7-5 syllables) and nothing else - no preamble, "
    "no explanation."
)

haiku_subagent = create_agent(model=MODEL, tools=[], system_prompt=HAIKU_PERSONA)


@tool
def haiku_bot(topic: str) -> str:
    """Delegate to a haiku-writing specialist subagent for the given topic."""
    result = haiku_subagent.invoke(
        {"messages": [{"role": "user", "content": f"Write a haiku about {topic}."}]}
    )
    return result["messages"][-1].content


def main():
    main_agent = create_agent(model=MODEL, tools=[haiku_bot])
    result = main_agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Use the haiku_bot tool to write a haiku about recursion. "
                        "Relay its output back to me verbatim."
                    ),
                }
            ]
        }
    )
    for msg in result["messages"]:
        print(f"[{type(msg).__name__}] {msg.content!r}")

    cost = 0.0
    for msg in result["messages"]:
        usage = getattr(msg, "usage_metadata", None)
        if usage:
            cost += usage.get("input_tokens", 0) * 1.0 / 1_000_000
            cost += usage.get("output_tokens", 0) * 5.0 / 1_000_000
    print(f"\n[cost_usd~ main agent only] {cost:.6f}")


if __name__ == "__main__":
    main()
