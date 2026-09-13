"""
Lesson 3 - system_prompt and model choice.

Mirrors lessons/03_system_prompt_and_model.py, with one structural
difference worth internalizing: the Claude Agent SDK has a claude_code
system_prompt PRESET (a built-in coding-assistant identity you can extend
via append=). LangChain's create_agent has no such preset at all -
system_prompt=None means a completely blank slate every time, and
system_prompt="..." is the ONLY way to give the agent any identity.
There's no "extend the built-in persona" option to demonstrate here,
because there is no built-in persona.

Demo 3 compares model tiers (haiku vs sonnet) on the same reasoning
question, standing in for the SDK lesson's effort=low/high comparison -
LangChain's create_agent has no first-class "effort" concept; capability
is instead controlled by which model you point it at.
"""

import sys

from dotenv import load_dotenv
from langchain.agents import create_agent

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

INTRO_TASK = "In one sentence, introduce yourself and describe your role for me."
REASON_TASK = "Is 17 a prime number? Answer with just yes or no and a one-sentence reason."

CUSTOM_PERSONA = (
    "You are Ruthless Reviewer, a terse senior code-review bot. "
    "Speak only in short, blunt statements. Never use filler pleasantries "
    "like 'I'd be happy to' or 'Great question'."
)

RATES = {
    "claude-haiku-4-5": (1.0 / 1_000_000, 5.0 / 1_000_000),
    "claude-sonnet-5": (2.0 / 1_000_000, 10.0 / 1_000_000),
}


def cost_of(model: str, usage: dict) -> float:
    if not usage:
        return 0.0
    in_rate, out_rate = RATES[model]
    return usage.get("input_tokens", 0) * in_rate + usage.get("output_tokens", 0) * out_rate


def run_demo(label: str, prompt: str, model: str, system_prompt=None):
    print(f"\n=== {label} ===")
    agent = create_agent(model=model, tools=[], system_prompt=system_prompt)
    result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
    final = result["messages"][-1]
    print(f"  [text] {final.content}")
    print(f"  [cost_usd~] {cost_of(model, final.usage_metadata):.6f}")


def main():
    run_demo("1. system_prompt=None (blank slate)", INTRO_TASK, "claude-haiku-4-5")
    run_demo(
        "2. custom string system_prompt",
        INTRO_TASK,
        "claude-haiku-4-5",
        system_prompt=CUSTOM_PERSONA,
    )
    run_demo(
        "3a. model='claude-haiku-4-5'",
        REASON_TASK,
        "claude-haiku-4-5",
        system_prompt=CUSTOM_PERSONA,
    )
    run_demo(
        "3b. model='claude-sonnet-5'",
        REASON_TASK,
        "claude-sonnet-5",
        system_prompt=CUSTOM_PERSONA,
    )


if __name__ == "__main__":
    main()
