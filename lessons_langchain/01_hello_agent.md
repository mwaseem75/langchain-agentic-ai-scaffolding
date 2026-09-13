# Lesson 1 — A Bare LLM Call vs. an Agent-Wrapped Call

**File:** `lessons_langchain/01_hello_agent.py`
**Companion lesson:** the matching concept in the `claude-agentic-ai-scaffolding` repo
**Model:** `claude-haiku-4-5`
**Verified cost:** ~$0.0007 total across both calls

## What this lesson is

The `claude-agent-sdk` curriculum started one level up — `query()` is always an
agent loop, even with `tools=[]`. LangChain draws a sharper line: a **plain chat
model call** and an **agent** are genuinely different objects with different
return shapes, and this lesson makes that distinction the entire point.

## Framework difference worth internalizing first

The Claude Agent SDK ships built-in tools (`Read`/`Edit`/`Bash`/`Glob`/...) because
it's a Python wrapper around the Claude Code CLI *engine*. **LangChain ships no
built-in tools at all** — it's a bring-your-own-tools framework wrapping a plain
chat model. There's no subprocess underneath a LangChain call, just an HTTP
request to the model provider's API. Every capability from here on is something
*you* define with `@tool` (Lesson 4).

LangChain also supports plain synchronous `.invoke()` — no `asyncio` boilerplate
required, unlike the SDK's async-only `query()`.

## Demo A — a bare model call

```python
llm = ChatAnthropic(model="claude-haiku-4-5")
response = llm.invoke(PROMPT)
```

Result: a single `AIMessage` object. One request, one response — no loop, no tool
consideration, nothing agentic about it at all.

```
[type] AIMessage
[text] An agentic LLM can autonomously plan and execute multi-step tasks...
[usage] {'input_tokens': 34, 'output_tokens': 73, ...}
```

## Demo B — the same prompt, agent-wrapped

```python
agent = create_agent(model="claude-haiku-4-5", tools=[])
result = agent.invoke({"messages": [{"role": "user", "content": PROMPT}]})
```

Even with `tools=[]` (identical to Demo A's actual capability — nothing to call),
`create_agent` returns a fundamentally different shape: a **message list**, not a
single response.

```
[HumanMessage] "In two sentences, what does 'agentic' mean..."
[AIMessage] 'An agentic LLM can autonomously break down complex tasks...'
```

`result["messages"]` is your own input `HumanMessage` echoed back, followed by the
model's `AIMessage` — LangGraph's `AgentState` always carries the full transcript,
even for a single turn with no tools.

## A real finding: no visible "thinking" here

Unlike `lessons/01_hello_query.py`, where a `ThinkingBlock` appeared even with zero
tools available, neither demo here shows any reasoning trace. LangChain's
`ChatAnthropic` does not automatically request extended/adaptive thinking the way
the Claude Code CLI does — it's an explicit opt-in via model kwargs
(`model_kwargs={"thinking": {"type": "adaptive"}}` or similar), not a default
behavior. Worth remembering: the two frameworks differ in more than API shape —
the underlying request they make to the same model isn't identical either.

## Reference

| Concept | Bare call (`ChatAnthropic`) | Agent call (`create_agent`) |
|---|---|---|
| Return type | Single `AIMessage` | `{"messages": [...]}` — full list |
| Loop? | None — one request, one response | LangGraph agent loop (still runs once here, since no tools to call) |
| Tools available | N/A | Whatever's passed to `tools=` |
| Async requirement | Neither — both support sync `.invoke()` and async `.ainvoke()` |

## Key takeaway

In LangChain, "agent" is not a mode flag on a chat call — it's a structurally
different object (`create_agent` returns a compiled LangGraph graph) with a
structurally different return shape (a message list, not a single message), even
in the degenerate zero-tools case.

## Try it yourself

- Print `type(agent)` to see the actual LangGraph `CompiledStateGraph` class name.
- Add `model_kwargs={"thinking": {"type": "adaptive"}}` to `ChatAnthropic` and see
  whether a reasoning trace becomes visible.
