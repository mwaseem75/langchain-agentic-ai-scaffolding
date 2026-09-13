"""
Lesson 2 - HumanInTheLoopMiddleware: LangChain's approval-gate equivalent.

Mirrors lessons/02_tools_and_permissions.py. The Claude Agent SDK's
permission_mode defaults to "ask" for risky built-in tools; LangChain has
the OPPOSITE default - per HumanInTheLoopMiddleware's own docstring, "If a
tool doesn't have an entry [in interrupt_on], it's auto-approved by
default." Nothing is gated unless you explicitly list it.

Two custom tools stand in for the SDK lesson's Edit/Bash pair:
  - write_note (edit-like)  -> NOT listed in interrupt_on -> auto-approved
  - run_shell  (bash-like)  -> interrupt_on={"run_shell": True} -> gated

A checkpointer + fixed thread_id are required for this to work at all:
resuming a paused graph after human review needs the run's state to be
persisted between the initial call and the resume call.
"""

import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

MODEL = "claude-haiku-4-5"

# claude-haiku-4-5 published rate: $1 / $5 per million input / output tokens.
INPUT_RATE = 1.0 / 1_000_000
OUTPUT_RATE = 5.0 / 1_000_000


def total_cost(result: dict) -> float:
    total = 0.0
    for msg in result.get("messages", []):
        usage = getattr(msg, "usage_metadata", None)
        if usage:
            total += usage.get("input_tokens", 0) * INPUT_RATE
            total += usage.get("output_tokens", 0) * OUTPUT_RATE
    return total


@tool
def write_note(content: str) -> str:
    """Record a short note (does not touch the real filesystem in this demo)."""
    return f"Note recorded: {content!r}"


@tool
def run_shell(command: str) -> str:
    """Run a shell command (simulated in this demo - not actually executed)."""
    return f"(simulated) ran: {command!r}"


def print_messages(result: dict):
    for msg in result.get("messages", []):
        print(f"    [{type(msg).__name__}] {msg.content!r}")


def main():
    checkpointer = InMemorySaver()
    agent = create_agent(
        model=MODEL,
        tools=[write_note, run_shell],
        middleware=[HumanInTheLoopMiddleware(interrupt_on={"run_shell": True})],
        checkpointer=checkpointer,
    )
    config = {"configurable": {"thread_id": "lesson2-demo"}}

    print("=== Turn 1: agent attempts both tools ===")
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "First call write_note with content 'hello from lesson 2'. "
                        "Then call run_shell with command 'echo permission test'."
                    ),
                }
            ]
        },
        config=config,
    )
    print_messages(result)

    if "__interrupt__" in result:
        interrupt = result["__interrupt__"][0]
        print(f"\n[PAUSED] interrupt payload: {interrupt.value}")

        print("\n=== Resuming with decision: approve ===")
        result2 = agent.invoke(
            Command(resume={"decisions": [{"type": "approve"}]}),
            config=config,
        )
        print_messages(result2)
        print(f"    [cost_usd~] {total_cost(result2):.6f}")
    else:
        print("\n[no interrupt was raised - unexpected for this demo]")

    print("\n=== Fresh thread: same task, this time REJECT the shell call ===")
    config_b = {"configurable": {"thread_id": "lesson2-demo-reject"}}
    result_b = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Call write_note with content 'second run'. "
                        "Then call run_shell with command 'rm -rf /important'."
                    ),
                }
            ]
        },
        config=config_b,
    )
    if "__interrupt__" in result_b:
        interrupt_b = result_b["__interrupt__"][0]
        print(f"[PAUSED] interrupt payload: {interrupt_b.value}")
        result_b2 = agent.invoke(
            Command(
                resume={
                    "decisions": [
                        {"type": "reject", "message": "Shell access denied for this demo."}
                    ]
                }
            ),
            config=config_b,
        )
        print_messages(result_b2)
        print(f"    [cost_usd~] {total_cost(result_b2):.6f}")


if __name__ == "__main__":
    main()
