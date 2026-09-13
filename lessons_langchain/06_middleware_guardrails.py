"""
Lesson 6 - custom middleware guardrails via @wrap_tool_call.

Mirrors lessons/06_hooks.py: same scenario (block a shell command
containing "rm -rf"), same two-command test (one harmless, one
dangerous), no other gate configured - so this guardrail is the ONLY
thing standing between the agent and running the dangerous command,
exactly like the SDK lesson's bypassPermissions + hook combination.

@wrap_tool_call decorates a (request, handler) function into a ready-to-use
AgentMiddleware instance - no manual instantiation needed, just drop it
into middleware=[...]. request.tool_call is a plain dict with 'name',
'args', 'id' keys (confirmed by reading the installed source directly).
Calling handler(request) actually runs the tool; NOT calling it - and
returning your own ToolMessage instead - is how you block it.
"""

import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools import tool

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

MODEL = "claude-haiku-4-5"
BLOCKED_PATTERN = "rm -rf"


@tool
def run_shell(command: str) -> str:
    """Run a shell command (simulated in this demo - not actually executed)."""
    return f"(simulated) ran: {command!r}"


@wrap_tool_call
def guard_dangerous_shell(request, handler):
    command = request.tool_call.get("args", {}).get("command", "")
    if request.tool_call["name"] == "run_shell" and BLOCKED_PATTERN in command:
        print(f"    [middleware] BLOCKING command={command!r}")
        return ToolMessage(
            content=f"Blocked by guardrail middleware: contains {BLOCKED_PATTERN!r}",
            tool_call_id=request.tool_call["id"],
        )
    print(f"    [middleware] allowing command={command!r}")
    return handler(request)


def main():
    agent = create_agent(model=MODEL, tools=[run_shell], middleware=[guard_dangerous_shell])
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Use run_shell to run these two commands, one at a time, and "
                        "report the result of each: "
                        "(1) echo hello from lesson 6  "
                        "(2) rm -rf ./lesson6-scratch-nonexistent-dir"
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
    print(f"\n[cost_usd~] {cost:.6f}")


if __name__ == "__main__":
    main()
