# Lesson 2 — `HumanInTheLoopMiddleware`: LangChain's Approval Gate

**File:** `lessons_langchain/02_human_in_the_loop.py`
**Companion lesson:** the matching concept in the `claude-agentic-ai-scaffolding` repo
**Model:** `claude-haiku-4-5`
**Verified cost:** ~$0.0045 total (two full approve/reject cycles)

## What this lesson is

The Claude Agent SDK's `permission_mode` defaults to gating risky tools until you
opt out (`acceptEdits`/`bypassPermissions`). LangChain's `HumanInTheLoopMiddleware`
has the **opposite default** — straight from its own docstring:

> "If a tool doesn't have an entry [in `interrupt_on`], it's auto-approved by
> default."

Nothing is gated unless you explicitly list it. This is a real, important
difference in default posture between the two frameworks, not just a naming
difference.

## The setup

Two custom tools stand in for the SDK lesson's `Edit`/`Bash` pair:

```python
@tool
def write_note(content: str) -> str:
    """Record a short note."""
    ...

@tool
def run_shell(command: str) -> str:
    """Run a shell command (simulated in this demo)."""
    ...

agent = create_agent(
    model=MODEL,
    tools=[write_note, run_shell],
    middleware=[HumanInTheLoopMiddleware(interrupt_on={"run_shell": True})],
    checkpointer=InMemorySaver(),
)
```

Only `run_shell` is listed in `interrupt_on` — `write_note` is never gated at all.

## Why a checkpointer is mandatory here (not optional, unlike Lesson 5)

When the graph hits an interrupt, execution literally **pauses mid-run**. Resuming
it on a later `.invoke()` call requires the graph's in-progress state to have been
persisted somewhere in between. Without `checkpointer=InMemorySaver()`, there is no
mechanism to resume at all — this is the one lesson in the curriculum where
statefulness isn't a nice-to-have, it's structurally required for the feature to
function.

## The interrupt/resume cycle

```python
config = {"configurable": {"thread_id": "lesson2-demo"}}
result = agent.invoke({"messages": [...]}, config=config)

if "__interrupt__" in result:
    interrupt = result["__interrupt__"][0]
    print(interrupt.value)   # the pending action request(s)

    result2 = agent.invoke(
        Command(resume={"decisions": [{"type": "approve"}]}),
        config=config,
    )
```

Verified by reading the installed `human_in_the_loop.py` source directly (not
assuming from docs): the middleware calls
`decisions = interrupt(hitl_request)["decisions"]` internally, which is exactly
the `{"decisions": [...]}` shape `Command(resume=...)` must supply. Each decision
is one of:

| `type` | Extra field | Effect |
|---|---|---|
| `"approve"` | — | Tool call runs as originally requested |
| `"reject"` | `"message"` | Tool call is skipped; the message becomes the tool's result, visible to the agent |
| `"edit"` | `"edited_action": {"name": ..., "args": {...}}` | Tool runs with modified arguments |
| `"respond"` | `"message"` | A custom message stands in for the tool result entirely |

## Results — both paths verified

**Approve:**
```
[PAUSED] interrupt payload: {'action_requests': [{'name': 'run_shell', ...}], ...}
[ToolMessage] "Note recorded: 'hello from lesson 2'"
[ToolMessage] "(simulated) ran: 'echo permission test'"
[AIMessage] "Done! I've successfully: 1. Written a note... 2. Ran the shell command..."
```

**Reject (fresh thread, different `thread_id`):**
```
[PAUSED] interrupt payload: {'action_requests': [{'name': 'run_shell', 'args': {'command': 'rm -rf /important'}, ...}]}
[ToolMessage] 'User rejected the tool call for `run_shell` with reason: Shell access denied for this demo.'
[ToolMessage] "Note recorded: 'second run'"
[AIMessage] "...the shell command `rm -rf /important` was rejected - shell access is denied..."
```

In both cases, `write_note` never paused at all — it ran immediately in the same
turn the model requested it, exactly as the "auto-approved by default" docstring
promised.

## A verification gotcha worth recording

Official doc summaries (fetched via an automated web-content tool while researching
this lesson) mentioned passing `version="v2"` to `.invoke()` as part of the
interrupt flow. Reading the installed `CompiledStateGraph.invoke()` signature
directly showed `version` actually controls **streaming chunk format**
(`stream_mode` v1 vs. v2), unrelated to interrupts, and defaults to `"v1"` — which
is exactly what this lesson uses successfully with no `version` argument at all.
**Lesson:** verify library behavior against the installed source before trusting
an AI-generated summary of documentation, even official documentation.

## Reference

| Concept | claude-agent-sdk | LangChain |
|---|---|---|
| Default posture | Ask/deny unless configured otherwise | **Auto-approve unless configured otherwise** |
| Gate mechanism | `permission_mode` + `can_use_tool` callback | `HumanInTheLoopMiddleware(interrupt_on={...})` |
| Pause signal | N/A (callback returns synchronously) | Graph literally pauses; `"__interrupt__"` key in result |
| Resume | N/A | `Command(resume={"decisions": [...]})` on the same `thread_id` |
| Requires persistence? | No | **Yes** — a checkpointer is mandatory |

## Key takeaway

LangChain's human-in-the-loop model is fundamentally *pause-and-resume*, not
*synchronous-callback* — the whole graph execution suspends, and resuming it later
is a first-class, checkpointer-backed operation rather than a function call
returning a decision inline.

## Try it yourself

- Change `interrupt_on={"run_shell": True}` to also gate `write_note` and observe
  two separate interrupts in the same turn.
- Try the `"edit"` decision type to change the shell command before it "runs."
