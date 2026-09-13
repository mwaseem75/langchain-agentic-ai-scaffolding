# LangChain Agentic AI Scaffolding

Nine small, working programs that teach you how LangChain's `create_agent`
actually behaves — not by reading the docs, but by running things, watching
them fail, and fixing them.

Every lesson here is a runnable Python script, paired with a write-up that
tells you exactly what happened when it ran: the real output, the real cost
in dollars, and the real errors I hit along the way — including one that
LangChain's own official documentation got wrong.

If you've read "LangChain is an agent framework" and wanted to know what that
actually means at the code level — not the marketing level — this is that.

## What `create_agent` actually is

LangChain's API has changed shape more than once (`AgentExecutor` →
LangGraph → the current `langchain` 1.x `create_agent`), so if you learned
this framework a year or two ago, some of what you knew is gone. Here's the
current shape:

```python
from langchain.agents import create_agent

agent = create_agent(
    model="claude-haiku-4-5",
    tools=[my_tool],
    system_prompt="...",
)
result = agent.invoke({"messages": [{"role": "user", "content": "..."}]})
```

The thing worth understanding up front: **LangChain ships zero built-in
tools.** No file reader, no shell, no web search, unless you bring one
yourself. That's the opposite bet from a framework like the Claude Agent SDK,
which wraps a whole coding CLI. LangChain is a blank canvas with excellent
scaffolding around it — `@tool` to define capabilities, `middleware=[...]` to
wrap the tool-call lifecycle, a checkpointer for memory. You build the agent
you actually want, piece by piece, and every piece in this repo is one you
can hand off to a real project.

## Who this is for

You're comfortable with Python and have probably called an LLM API directly
before. You want a working mental model of tool calling, human-in-the-loop
approval, statefulness, and guardrails in LangChain specifically — not a
30,000-foot conceptual overview, but the actual function signatures and the
actual failure modes.

## Setup

```bash
uv sync
cp .env.example .env   # then paste in your real Anthropic key
```

```bash
uv run lessons_langchain/01_hello_agent.py
```

Every lesson runs the same way. Almost everything defaults to
`claude-haiku-4-5`, so the whole nine-lesson run costs a few cents in total —
cheap enough to run twice if something doesn't click the first time.

## The lessons

| # | Run it | Read about it | What it actually teaches |
|---|--------|----------------|---------------------------|
| 1 | `lessons_langchain/01_hello_agent.py` | [01_hello_agent.md](lessons_langchain/01_hello_agent.md) | Why `create_agent(tools=[]).invoke()` returns a message list, not a single response — even when it has nothing to do |
| 2 | `lessons_langchain/02_human_in_the_loop.py` | [02_human_in_the_loop.md](lessons_langchain/02_human_in_the_loop.md) | Pausing a running agent mid-tool-call and resuming it later with an approve/reject decision |
| 3 | `lessons_langchain/03_system_prompt_and_model.py` | [03_system_prompt_and_model.md](lessons_langchain/03_system_prompt_and_model.md) | LangChain agents start from a genuinely blank identity — there's no built-in persona to extend |
| 4 | `lessons_langchain/04_custom_tools.py` | [04_custom_tools.md](lessons_langchain/04_custom_tools.md) | `@tool`, direct in-process state access, and why there's no naming-prefix trap here |
| 5 | `lessons_langchain/05_stateful_agent.py` | [05_stateful_agent.md](lessons_langchain/05_stateful_agent.md) | The same agent object, stateful or stateless, depending only on whether you attach a checkpointer |
| 6 | `lessons_langchain/06_middleware_guardrails.py` | [06_middleware_guardrails.md](lessons_langchain/06_middleware_guardrails.md) | `@wrap_tool_call` — a guardrail that runs underneath the permission system entirely |
| 7 | `lessons_langchain/07_subagents.py` | [07_subagents.md](lessons_langchain/07_subagents.md) | Delegating to a specialist is just... another agent, wrapped in a function. No special primitive needed |
| 8 | `lessons_langchain/08_mcp_external_server.py` | [08_mcp_external_server.md](lessons_langchain/08_mcp_external_server.md) | Connecting to a real external process over MCP — and the async-only trap that broke the first attempt |
| 9 | `lessons_langchain/09_capstone.py` | [09_capstone.md](lessons_langchain/09_capstone.md) | "Repo Housekeeper" — two independent guardrails on the same tool, scoped so they never even have to compete |

## A few things worth knowing before you hit them yourself

**The default posture is the opposite of what you'd guess.**
`HumanInTheLoopMiddleware` auto-approves any tool you *don't* explicitly list.
Coming from a background where APIs default to cautious, this trips people
up — Lesson 2 shows exactly where.

**Official docs told me to use a parameter that does something else
entirely.** An AI-generated summary of LangChain's own documentation
suggested passing `version="v2"` to `.invoke()` as part of resuming a paused
agent. Reading the actual installed source showed `version` controls
streaming chunk format and has nothing to do with interrupts. It worked fine
with no `version` argument at all. Lesson 2 has the receipts — always check
the source that's actually installed, not a summary of a page about it.

**MCP-adapter tools are async-only, and nothing tells you that until you hit
it.** `agent.invoke()` on an agent holding a LangChain-MCP tool fails with
`StructuredTool does not support sync invocation`. The fix is `ainvoke()`.
Lesson 8 shows the failure and the fix, plus a real cross-package dependency
conflict I ran into installing `langchain-mcp-adapters` in the first place.

## If you want the Claude Agent SDK version too

There's a companion repo, **[claude-agentic-ai-scaffolding](https://github.com/mwaseem75/claude-agentic-ai-scaffolding)**,
covering the same nine concepts on Anthropic's own Claude Agent SDK — same
scenarios, same "Repo Housekeeper" capstone, a genuinely different
philosophy (batteries-included coding CLI vs. bring-your-own-everything).
Worth running both if you're trying to figure out which parts of "agentic"
are universal and which are just one framework's opinion.

## License

MIT. Use this however is useful to you — fork it, strip it down, teach from
it, whatever.
