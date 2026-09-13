# Lesson 5 — Checkpointer + `thread_id` vs. No Checkpointer

**File:** `lessons_langchain/05_stateful_agent.py`
**Run it:** `uv run lessons_langchain/05_stateful_agent.py`
**Companion lesson:** the matching concept in the `claude-agentic-ai-scaffolding` repo
**Verified cost:** negligible (4 short calls, well under $0.01)

## What this lesson is

Same experiment as the SDK curriculum's Lesson 5, and the same clean result — but
a structurally different mechanism produces it. The Claude Agent SDK had two
*different classes* (`query()` vs. `ClaudeSDKClient`) for stateless vs. stateful.
LangChain uses the **same** `create_agent(...)` object in both demos below —
statefulness is entirely a property of whether a `checkpointer` is attached and
whether calls share a `thread_id`.

## Demo A — stateful

```python
agent = create_agent(model=MODEL, tools=[], checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "lesson5-demo"}}

agent.invoke({"messages": [{"role": "user", "content": TURN_1}]}, config=config)
agent.invoke({"messages": [{"role": "user", "content": TURN_2}]}, config=config)
```

Reusing `config` (same `thread_id`) across both calls is what links them into one
conversation — the checkpointer persists the message history between calls under
that key.

## Demo B — stateless

```python
agent = create_agent(model=MODEL, tools=[])  # no checkpointer at all

agent.invoke({"messages": [{"role": "user", "content": TURN_1}]})
agent.invoke({"messages": [{"role": "user", "content": TURN_2}]})
```

No `checkpointer`, no `config` — each `.invoke()` is a fully independent run.

## Results

| | Turn 1 | Turn 2 ("What's double my favorite number?") |
|---|---|---|
| **Stateful (checkpointer + thread_id)** | *"That's a great number! Classic choice."* | **"Double 42 is 84."** — remembered |
| **Stateless (no checkpointer)** | *"That's a great choice—the ultimate answer to life, the universe, and everything!"* | **"I don't know what your favorite number is!"** — no shared history |

Identical outcome to the original curriculum's Lesson 5, via a different
mechanism entirely.

## Reference

| | claude-agent-sdk | LangChain |
|---|---|---|
| Stateless entry point | `query()` — a function | `create_agent(...)` with **no** `checkpointer` |
| Stateful entry point | `ClaudeSDKClient` — a different class, `async with` | The **same** `create_agent(...)`, with a `checkpointer` + reused `thread_id` |
| What links turns together | An open connection (`client.query()` × N) | A shared `thread_id` in `config` |
| Can one agent object serve both modes? | No — different classes | **Yes** — statefulness is orthogonal to how the agent was built |

## Key takeaway

In LangChain, statefulness isn't a choice of *which object* you construct — it's a
choice of *whether you attach a checkpointer and reuse a thread_id*. The same
compiled agent graph can be invoked statelessly (omit `config`) or statefully
(reuse `config`) call to call. This also explains why Lesson 2's interrupt/resume
flow required a checkpointer: pausing and resuming a run *is* a form of
statefulness, just within a single logical turn instead of across turns.

## Try it yourself

- Reuse the *stateful* agent object from Demo A but call it once more with a
  **different** `thread_id` and confirm it doesn't remember the favorite number
  either — statefulness is per-thread, not per-agent-object.
- Swap `InMemorySaver()` for a persistent checkpointer (e.g. a SQLite-backed one,
  if installed) and confirm memory survives a process restart, which
  `InMemorySaver` cannot do.
