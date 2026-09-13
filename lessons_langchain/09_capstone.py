"""
Lesson 9 - capstone: "Repo Housekeeper" rebuilt in LangChain.

Mirrors lessons/09_capstone.py's exact scenario and even its persona text,
combining lessons 2, 3, 4, and 6 of THIS folder:

  - file_stats: a real, deterministic @tool (lesson 4)
  - guard_dangerous_shell: a @wrap_tool_call guardrail blocking any
    run_shell command containing "rm -rf", unconditionally, no human
    involved (lesson 6)
  - HumanInTheLoopMiddleware, scoped with a `when` predicate to ONLY
    interrupt run_shell calls containing "sudo" - everything else
    (including the harmless echo command) is auto-approved (lesson 2)
  - system_prompt: the same scoped "Repo Housekeeper" persona (lesson 3)

Two independent layers, exactly like the SDK capstone: the wrap_tool_call
guard catches "rm -rf" automatically; the HITL gate additionally catches
"sudo" but requires a real approve/reject decision (resumed the same way
as lesson 2). Because HITL's `when` predicate only fires on "sudo", the
two layers never race each other - "rm -rf" never reaches HITL at all
regardless of middleware ordering, so there's no ambiguity to test around.
"""

import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

MODEL = "claude-haiku-4-5"
REPO_ROOT = Path(__file__).resolve().parent.parent

PERSONA = (
    "You are Repo Housekeeper, a careful and terse assistant for light "
    "repository hygiene tasks. You only inspect files and report findings - "
    "you never delete, move, or overwrite anything. When a tool or command "
    "is blocked by a safety guardrail, report that plainly instead of "
    "trying to work around it."
)


@tool
def file_stats(path: str) -> str:
    """Report line count, word count, and TODO/FIXME markers for a file."""
    p = Path(path)
    if not p.is_absolute():
        p = REPO_ROOT / p
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as e:
        return f"Error reading {p}: {e}"

    lines = text.splitlines()
    markers = [ln.strip() for ln in lines if "TODO" in ln or "FIXME" in ln]
    summary = (
        f"{p.name}: {len(lines)} lines, {len(text.split())} words, "
        f"{len(markers)} TODO/FIXME marker(s)"
    )
    if markers:
        summary += "\n  " + "\n  ".join(markers)
    return summary


@tool
def run_shell(command: str) -> str:
    """Run a shell command (simulated in this demo - not actually executed)."""
    return f"(simulated) ran: {command!r}"


@wrap_tool_call
def guard_dangerous_shell(request, handler):
    command = request.tool_call.get("args", {}).get("command", "")
    if request.tool_call["name"] == "run_shell" and "rm -rf" in command:
        print(f"    [wrap_tool_call] BLOCKING (dangerous pattern) command={command!r}")
        return ToolMessage(
            content="Blocked by guardrail middleware: contains 'rm -rf'",
            tool_call_id=request.tool_call["id"],
        )
    return handler(request)


def sudo_only(request) -> bool:
    return "sudo" in request.tool_call.get("args", {}).get("command", "")


def print_messages(result: dict):
    for msg in result.get("messages", []):
        print(f"    [{type(msg).__name__}] {msg.content!r}")


def main():
    checkpointer = InMemorySaver()
    agent = create_agent(
        model=MODEL,
        tools=[file_stats, run_shell],
        system_prompt=PERSONA,
        middleware=[
            guard_dangerous_shell,
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "run_shell": {"allowed_decisions": ["approve", "reject"], "when": sudo_only}
                }
            ),
        ],
        checkpointer=checkpointer,
    )
    config = {"configurable": {"thread_id": "lesson9-capstone"}}

    print("=== Turn 1: inspect files, then try three shell commands ===")
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Use file_stats to inspect utils.py and "
                        "lessons_langchain/01_hello_agent.py (both relative to the repo "
                        "root), and report what it finds for each. "
                        "Then, to test your safety guardrails, try these three run_shell "
                        "commands one at a time and report what happens to each: "
                        "(1) echo housekeeping check ok  "
                        "(2) rm -rf ./should-not-run  "
                        "(3) sudo echo should-also-not-run"
                    ),
                }
            ]
        },
        config=config,
    )
    print_messages(result)

    if "__interrupt__" in result:
        interrupt = result["__interrupt__"][0]
        print(f"\n[PAUSED for human review] {interrupt.value}")
        print("\n=== Resuming with decision: reject (sudo denied) ===")
        result2 = agent.invoke(
            Command(
                resume={
                    "decisions": [
                        {"type": "reject", "message": "sudo is not allowed for this agent."}
                    ]
                }
            ),
            config=config,
        )
        print_messages(result2)

        cost = 0.0
        for msg in result2.get("messages", []):
            usage = getattr(msg, "usage_metadata", None)
            if usage:
                cost += usage.get("input_tokens", 0) * 1.0 / 1_000_000
                cost += usage.get("output_tokens", 0) * 5.0 / 1_000_000
        print(f"\n[cost_usd~] {cost:.6f}")


if __name__ == "__main__":
    main()
