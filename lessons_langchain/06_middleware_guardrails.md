# Lesson 6 — Custom Middleware Guardrails via `@wrap_tool_call`

**File:** `lessons_langchain/06_middleware_guardrails.py`
**Run it:** `uv run lessons_langchain/06_middleware_guardrails.py`
**Companion lesson:** the matching concept in the `claude-agentic-ai-scaffolding` repo
**Verified cost:** $0.0034 (worked on the first run)

## What this lesson is

The exact same scenario as the SDK curriculum's Lesson 6: block any shell command
containing `rm -rf`, with no other gate configured — this middleware is the *only*
thing standing between the agent and running the dangerous command.

## The middleware

```python
@wrap_tool_call
def guard_dangerous_shell(request, handler):
    command = request.tool_call.get("args", {}).get("command", "")
    if request.tool_call["name"] == "run_shell" and BLOCKED_PATTERN in command:
        return ToolMessage(
            content=f"Blocked by guardrail middleware: contains {BLOCKED_PATTERN!r}",
            tool_call_id=request.tool_call["id"],
        )
    return handler(request)
```

`@wrap_tool_call` turns a plain `(request, handler)` function into a ready-to-use
`AgentMiddleware` instance — no manual class definition or instantiation needed,
just drop it straight into `middleware=[...]`. Confirmed by reading the decorator's
installed source directly: `request.tool_call` is a plain dict with `name`, `args`,
`id` keys.

**Calling `handler(request)`** actually executes the tool and returns its real
result. **Not calling it** — returning your own `ToolMessage` instead — is exactly
how you block a call. There's no separate "deny" return type; the block *is* the
substitution of a synthetic result for the real one.

## Results

```
[middleware] allowing command='echo hello from lesson 6'
[middleware] BLOCKING command='rm -rf ./lesson6-scratch-nonexistent-dir'

[ToolMessage] "(simulated) ran: 'echo hello from lesson 6'"
[ToolMessage] "Blocked by guardrail middleware: contains 'rm -rf'"

[AIMessage] '**Results:** 1. echo... - Successfully executed... 2. rm -rf... - Blocked
by guardrail middleware. The system has security protections that prevent execution
of rm -rf commands...'
```

Identical shape to the SDK's Lesson 6 result: the harmless command runs and its
real output reaches the model; the dangerous one never runs at all, and the model
correctly reports it as blocked rather than hallucinating a result.

## Reference

| Concept | claude-agent-sdk (`PreToolUse` hook) | LangChain (`@wrap_tool_call`) |
|---|---|---|
| Registration | `hooks={"PreToolUse": [HookMatcher(matcher="Bash", hooks=[...])]}` | `middleware=[guard_dangerous_shell]` on `create_agent` |
| Signature | `async def hook(input, tool_use_id, context) -> HookJSONOutput` | `def guard(request, handler) -> ToolMessage \| Command` |
| Allow | Return `{}` (no decision) — falls through to permission system | Call `handler(request)` and return its result |
| Deny | Return a `hookSpecificOutput` dict with `permissionDecision: "deny"` | Return your own `ToolMessage` instead of calling `handler` |
| Independent of other gates? | Yes — fires even under `bypassPermissions` | Yes — this demo has no `HumanInTheLoopMiddleware` at all, and the block still works |

## Key takeaway

Both frameworks land on the same design principle even though the mechanics
differ: a guardrail that must never be silently skippable belongs at the
tool-execution-wrapping layer (`PreToolUse` hooks / `wrap_tool_call` middleware),
not at the permission-approval layer (`can_use_tool` / `HumanInTheLoopMiddleware`)
— because the approval layer can be configured away, and the execution-wrapping
layer sits *underneath* every tool call regardless of any permission
configuration.

## Try it yourself

- Combine this middleware with Lesson 2's `HumanInTheLoopMiddleware` in the same
  `middleware=[...]` list and observe both running against the same tool call.
- Change the guardrail to modify the command instead of blocking it entirely,
  using `request.override(tool_call={...})` before calling `handler`.
