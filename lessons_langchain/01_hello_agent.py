"""
Lesson 1 - a bare LLM call vs. an agent-wrapped call.

Mirrors lessons/01_hello_query.py from the claude-agent-sdk curriculum, but
starts one level lower: LangChain draws a sharp line between a plain chat
model call (ChatAnthropic().invoke() - one request, one response, no loop)
and an *agent* (create_agent(...).invoke() - even with zero tools, the
call goes through LangGraph's agent loop and returns a full message list,
not a single response object).

Unlike the Claude Agent SDK, LangChain has no built-in tools at all (no
Read/Edit/Bash) - it's a bring-your-own-tools framework wrapping a plain
chat model, not a wrapper around a batteries-included coding CLI. That's
why Demo A below just calls the model directly - there's no CLI subprocess
underneath it, only an HTTP request to the Anthropic API.

LangChain also supports plain synchronous .invoke() (no asyncio needed),
unlike the Claude Agent SDK's async-only query().
"""

import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_anthropic import ChatAnthropic

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

MODEL = "claude-haiku-4-5"
PROMPT = (
    "In two sentences, what does 'agentic' mean for an LLM, "
    "as opposed to a plain chat completion?"
)

# claude-haiku-4-5 published rate: $1 / $5 per million input / output tokens.
# LangChain doesn't expose a total_cost_usd field like ResultMessage did, so
# every lesson in this folder computes an approximate cost from usage_metadata.
INPUT_RATE = 1.0 / 1_000_000
OUTPUT_RATE = 5.0 / 1_000_000


def cost_of(usage: dict) -> float:
    if not usage:
        return 0.0
    return usage.get("input_tokens", 0) * INPUT_RATE + usage.get("output_tokens", 0) * OUTPUT_RATE


def main():
    print("=== Demo A: bare ChatAnthropic().invoke() - no agent loop ===")
    llm = ChatAnthropic(model=MODEL)
    response = llm.invoke(PROMPT)
    print(f"[type] {type(response).__name__}")
    print(f"[text] {response.content}")
    print(f"[usage] {response.usage_metadata}")
    print(f"[cost_usd~] {cost_of(response.usage_metadata):.6f}")

    print("\n=== Demo B: create_agent(tools=[]).invoke() - agent-wrapped ===")
    agent = create_agent(model=MODEL, tools=[])
    result = agent.invoke({"messages": [{"role": "user", "content": PROMPT}]})
    for msg in result["messages"]:
        print(f"[{type(msg).__name__}] {msg.content!r}")
    final = result["messages"][-1]
    print(f"[usage] {final.usage_metadata}")
    print(f"[cost_usd~] {cost_of(final.usage_metadata):.6f}")


if __name__ == "__main__":
    main()
