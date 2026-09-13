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

## Agentic AI in one paragraph, and what these two repos actually cover

"Agentic" gets thrown around a lot, so here's the plain version. A normal LLM
call takes text in, gives text out, and stops there. An agent keeps going — it
decides which tool to call, looks at what came back, decides what to do next,
and repeats that loop by itself until the task is done or it needs your
sign-off to continue. That loop, plus everything wrapped around it — which
tools it's allowed to touch, who approves what, whether it remembers earlier
turns, what stops it from doing something destructive — is what "agentic AI
framework" means once you strip away the marketing. Everything else is
implementation detail.

This repo and its sibling, **[claude-agentic-ai-scaffolding](https://github.com/mwaseem75/claude-agentic-ai-scaffolding)**,
teach that scaffolding through the same nine ideas — once on LangChain, once
on the Claude Agent SDK — so you can tell which parts are universal and which
are just one framework's opinion:

1. **The agent loop itself** — what actually streams back when an agent runs, beyond a single response
2. **Permissions and approval gates** — who decides whether a risky action actually executes
3. **Identity and model choice** — giving the agent a persona, and what changes when you swap models
4. **Custom tools** — teaching the agent to do something it couldn't do on its own
5. **Statefulness** — the difference between an agent that remembers your last message and one that doesn't
6. **Guardrails that can't be switched off** — a safety rule that survives even a permissive configuration
7. **Delegating to a specialist** — one agent handing a subtask to another
8. **Talking to something external** — connecting a tool that runs in a completely separate process
9. **A capstone** — combining all of the above into one small agent that's actually safe to run unattended

Work through both repos back to back and you end up with a tested mental model
of agentic AI, not just familiarity with one framework's API surface.

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
