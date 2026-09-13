# Lesson 9 — Capstone: "Repo Housekeeper" Rebuilt in LangChain

**File:** `lessons_langchain/09_capstone.py`
**Run it:** `uv run lessons_langchain/09_capstone.py`
**Verified cost:** $0.008 (worked on the first run)

## What this lesson is

"Repo Housekeeper" — a small agent that only inspects files and structurally
cannot edit or delete anything, wired up with two independent, layered
guardrails. It pulls together everything from Lessons 2–6 of this repo into one
coherent design.

## The four ingredients, combined

```python
agent = create_agent(
    model=MODEL,
    tools=[file_stats, run_shell],
    system_prompt=PERSONA,                              # lesson 3
    middleware=[
        guard_dangerous_shell,                           # lesson 6 - wrap_tool_call
        HumanInTheLoopMiddleware(                         # lesson 2 - HITL
            interrupt_on={
                "run_shell": {"allowed_decisions": ["approve", "reject"], "when": sudo_only}
            }
        ),
    ],
    checkpointer=checkpointer,                            # required for HITL to resume
)
```

`file_stats` (lesson 4's custom-tool pattern) is never gated at all — it's
harmless and deterministic, so it just runs.

## Avoiding an ordering question entirely, by design

Two independent guardrails both watch `run_shell`, which raises a natural
question: which one wins if they'd both apply to the same call? This lesson
sidesteps that ambiguity rather than guessing at middleware execution order:

- `guard_dangerous_shell` (`@wrap_tool_call`) blocks any command containing
  `"rm -rf"`, **unconditionally**, no human involved.
- `HumanInTheLoopMiddleware`'s `when` predicate is scoped to fire **only** when
  the command contains `"sudo"`:
  ```python
  def sudo_only(request) -> bool:
      return "sudo" in request.tool_call.get("args", {}).get("command", "")
  ```

Since the two triggers (`"rm -rf"` vs. `"sudo"`) never overlap on the same
command in this demo, there's no case where both middleware layers actually
compete for the same call — each guards its own distinct risk pattern, cleanly.

## Results — all three guardrail tests, verified

```
1. echo housekeeping check ok      -> ALLOWED, ran immediately
2. rm -rf ./should-not-run         -> BLOCKED by wrap_tool_call guard (no pause at all)
3. sudo echo should-also-not-run   -> PAUSED for human review, then REJECTED on resume
```

The interrupt payload for command 3, confirming the `when` predicate worked
exactly as scoped (nothing fired for commands 1 or 2):

```python
{'action_requests': [{'name': 'run_shell', 'args': {'command': 'sudo echo should-also-not-run'}, ...}],
 'review_configs': [{'action_name': 'run_shell', 'allowed_decisions': ['approve', 'reject']}]}
```

`file_stats` results, real numbers from actually reading the files:

```
utils.py: 19 lines, 69 words, 0 TODO/FIXME marker(s)
lessons_langchain/01_hello_agent.py: 69 lines, 312 words, 0 TODO/FIXME marker(s)
```

Claude's final summary correctly described all three outcomes without confusing
"blocked automatically" with "blocked after review" — the model tracked the
distinction between the two gates on its own.

## Design principles this capstone demonstrates

1. **Different tools, different postures.** `file_stats` (read-only, deterministic)
   gets no gate at all; `run_shell` (open-ended) gets two.
2. **Scope your interrupts precisely.** A blanket `interrupt_on={"run_shell": True}`
   would have paused on the harmless `echo` command too — the `when` predicate
   keeps human review reserved for the pattern that actually warrants it.
3. **Automatic and human-reviewed guardrails can coexist on the same tool**,
   each watching for a different risk signature, without needing to reason about
   which one "wins" — as long as their trigger conditions don't overlap.

## Everything this curriculum covered, in one table

| # | Concept | Where it lives in LangChain |
|---|---|---|
| 1 | The agent message loop | `create_agent(...).invoke()` returns a message list, not a single response |
| 2 | Permission / approval gates | `HumanInTheLoopMiddleware` + `Command(resume=...)` |
| 3 | Identity and model choice | `system_prompt=` string (always a blank slate), model tier |
| 4 | Custom tools | `@tool` |
| 5 | Statefulness | checkpointer + `thread_id` vs. none |
| 6 | Unskippable guardrails | `@wrap_tool_call` middleware |
| 7 | Delegating to a specialist | subagent-as-tool (`create_agent` wrapped in `@tool`) |
| 8 | External tool servers | `langchain-mcp-adapters` (async-only) |
| 9 | Layered guardrails, combined | `wrap_tool_call` + scoped `HumanInTheLoopMiddleware`, together |

## Key takeaway

By the time you reach this lesson, you've built the same defense-in-depth
thinking that shows up in every serious agent deployment: structural limits on
what a tool can even do, automatic guardrails that can't be configured away,
and human-reviewed gates reserved for the calls that actually warrant a second
look. LangChain gets you there with `@tool`, `middleware=[...]`, and a
checkpointer — no framework-specific "permission system" required, just
ordinary functions wired together deliberately.

## Try it yourself

- Add a third guardrail pattern (e.g. blocking `curl`/`wget`) as either another
  `wrap_tool_call` layer or another `when`-scoped HITL entry.
- Try approving the `sudo` command instead of rejecting it, and observe the
  simulated command actually "running."
