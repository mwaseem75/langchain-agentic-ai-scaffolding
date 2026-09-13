# Lesson 7 — The Subagents-as-Tools Pattern

**File:** `lessons_langchain/07_subagents.py`
**Run it:** `uv run lessons_langchain/07_subagents.py`
**Companion lesson:** the matching concept in the `claude-agentic-ai-scaffolding` repo
**Verified cost:** $0.0017 (main agent only — see caveat below)

## What this lesson is

Same scenario as the SDK curriculum's Lesson 7 — delegate haiku-writing to a
specialist — but LangChain has no dedicated "subagent" primitive at all. A
subagent is just **another `create_agent(...)`**, wrapped in a plain `@tool`
function:

```python
haiku_subagent = create_agent(model=MODEL, tools=[], system_prompt=HAIKU_PERSONA)

@tool
def haiku_bot(topic: str) -> str:
    """Delegate to a haiku-writing specialist subagent for the given topic."""
    result = haiku_subagent.invoke(
        {"messages": [{"role": "user", "content": f"Write a haiku about {topic}."}]}
    )
    return result["messages"][-1].content

main_agent = create_agent(model=MODEL, tools=[haiku_bot])
```

The parent agent sees `haiku_bot` as an ordinary tool — it has no idea there's a
whole other agent running underneath. This is "the subagents pattern" LangChain's
own docs recommend over the older, now-unmaintained `langgraph-supervisor`
library.

## Results — clean on the first run, no surprises

```
[AIMessage] [tool_use: haiku_bot(topic='recursion')]
[ToolMessage] 'Function calls itself\nLayers of reflection deep\nBase case saves the day'
[AIMessage] 'Here is the haiku about recursion:\n\nFunction calls itself\n...'
```

## The clearest contrast with the SDK version

The Claude Agent SDK's Lesson 7 was the messiest lesson in that whole curriculum —
subagents run as **background tasks by default** (confirmed via `is_backgrounded:
True`, unaffected by `AgentDefinition.background=False`), producing a noisy
two-turn stream with duplicate `ResultMessage`s and dozens of `thinking_tokens`
progress pings.

**None of that exists here.** `haiku_subagent.invoke(...)` is a plain, synchronous,
blocking function call — it runs to completion inside the tool function, in the
same process, before the tool even returns. There's no background-task
infrastructure to interact with, because there's no special "subagent" concept in
the framework to begin with — it's ordinary function composition.

## A real caveat, worth stating plainly

The `[cost_usd~ main agent only]` label is deliberate: this script's cost
calculation only walks `result["messages"]` from the **main** agent's `.invoke()`
call. The haiku subagent's own `.invoke()` inside the tool function has its own
token usage that never appears in that list — it's a separate LLM call with its
own real cost, simply not captured by this script's accounting. A production
version of this pattern would need to explicitly propagate or log the subagent's
usage too.

## Reference

| | claude-agent-sdk | LangChain |
|---|---|---|
| Subagent definition | `AgentDefinition(description, prompt, model, tools, ...)` | Just another `create_agent(...)` |
| Invocation mechanism | Built-in `Agent` tool, `agents={"name": AgentDefinition(...)}` | A `@tool`-wrapped function calling `.invoke()` |
| Execution model | Background task, two-turn stream, by default | Synchronous, blocking, single call |
| Framework-level "subagent" concept | Yes — a first-class option | No — plain function composition |

## Key takeaway

What the SDK curriculum needed a dedicated `AgentDefinition` + `Agent` tool +
background-task system to express, LangChain achieves with nothing more than "a
function that happens to call `.invoke()` on another agent." Simpler, but it also
means you get none of the SDK's built-in progress-tracking or background
concurrency for free — you'd build that yourself if you needed it.

## Try it yourself

- Make `haiku_bot` accept a `style` parameter and pass it through to the
  subagent's prompt.
- Add usage-tracking to the tool function itself, so the subagent's real cost is
  captured alongside the main agent's.
