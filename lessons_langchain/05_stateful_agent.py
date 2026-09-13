"""
Lesson 5 - checkpointer + thread_id (stateful) vs. no checkpointer (stateless).

Mirrors lessons/05_stateful_client.py exactly: tell the agent a fact, then
ask a follow-up that depends on remembering it. LangChain's statefulness
is a property of the CHECKPOINTER + a fixed thread_id, not of a special
"client" class the way ClaudeSDKClient was - the create_agent object
itself is identical in both demos below; only the presence of a
checkpointer (and reusing the same thread_id across calls) differs.
"""

import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

MODEL = "claude-haiku-4-5"
TURN_1 = "My favorite number is 42. Just acknowledge that in a few words."
TURN_2 = "What's double my favorite number?"


def print_last(result: dict):
    final = result["messages"][-1]
    print(f"  [text] {final.content}")


def demo_stateful():
    print("=== Demo A: checkpointer + fixed thread_id (stateful) ===")
    agent = create_agent(model=MODEL, tools=[], checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "lesson5-demo"}}
    for turn in (TURN_1, TURN_2):
        print(f"> {turn}")
        result = agent.invoke({"messages": [{"role": "user", "content": turn}]}, config=config)
        print_last(result)


def demo_stateless():
    print("\n=== Demo B: no checkpointer (stateless) ===")
    agent = create_agent(model=MODEL, tools=[])  # no checkpointer at all
    for turn in (TURN_1, TURN_2):
        print(f"> {turn}")
        result = agent.invoke({"messages": [{"role": "user", "content": turn}]})
        print_last(result)


def main():
    demo_stateful()
    demo_stateless()


if __name__ == "__main__":
    main()
