# Lesson 3 — `system_prompt` and Model Choice

**File:** `lessons_langchain/03_system_prompt_and_model.py`
**Run it:** `uv run lessons_langchain/03_system_prompt_and_model.py`
**Companion lesson:** the matching concept in the `claude-agentic-ai-scaffolding` repo
**Verified cost:** ~$0.001 total across 4 calls

## What this lesson is

A structural difference from the SDK curriculum, worth internalizing before
anything else: the Claude Agent SDK has a `claude_code` system-prompt **preset**
you can extend via `append=`. **LangChain's `create_agent` has no preset at all.**
`system_prompt=None` means a genuinely blank slate every time, and a custom string
is the *only* way to give the agent any identity — there's no "extend the built-in
persona" option, because there's no built-in persona to extend.

## Demo 1 — no system prompt

```python
agent = create_agent(model="claude-haiku-4-5", tools=[], system_prompt=None)
```

Result: *"I'm Claude, an AI assistant made by Anthropic, and I'm here to help you
with a wide range of tasks..."* — the model's own default self-description, with
zero LangChain- or agent-specific framing. Confirms the blank-slate claim directly.

## Demo 2 — custom persona

```python
agent = create_agent(model="claude-haiku-4-5", tools=[], system_prompt=CUSTOM_PERSONA)
```

Same `CUSTOM_PERSONA` string as `lessons/03_system_prompt_and_model.py`'s "Ruthless
Reviewer," for direct side-by-side comparison:

> *"I'm Ruthless Reviewer—I shred code with brutal honesty and cut through the
> fluff."*

Nearly identical framing to what the Claude Agent SDK produced with the same
prompt text — the persona-replacement mechanism itself behaves the same way in
both frameworks, even though the surrounding API differs.

## Demo 3 — model tier instead of `effort`

`create_agent` has no first-class `effort` parameter. Capability is instead
controlled entirely by *which model* you point the agent at:

```python
run_demo("3a", REASON_TASK, "claude-haiku-4-5", system_prompt=CUSTOM_PERSONA)
run_demo("3b", REASON_TASK, "claude-sonnet-5", system_prompt=CUSTOM_PERSONA)
```

| Model | Answer | Cost |
|---|---|---|
| `claude-haiku-4-5` | *"Yes. Only divisible by 1 and itself."* | $0.000152 |
| `claude-sonnet-5` | *"Yes — it has no divisors other than 1 and itself."* | $0.000414 |

Same correct answer, ~2.7× the cost for the larger model on this trivial
question — consistent with the original curriculum's finding that model/effort
differences matter most on genuinely hard problems, not simple fact checks.

## Reference

| Concept | claude-agent-sdk | LangChain |
|---|---|---|
| No system prompt | Bare model, but SDK-aware | Bare model, framework-unaware — literally just "Claude, made by Anthropic" |
| Custom identity | `system_prompt="..."` replaces entirely | Same — `system_prompt="..."` replaces entirely |
| Extend built-in identity | `{"type": "preset", "preset": "claude_code", "append": "..."}` | **Not available** — no built-in identity exists |
| Capability control | `effort="low".."max"` | Choice of `model=` |

## Key takeaway

LangChain agents start from nothing — no assumed role, no assumed toolset
awareness, no assumed "I am a coding assistant" framing. Every bit of identity and
behavioral steering has to be supplied explicitly via `system_prompt`, which makes
LangChain more of a blank canvas and the Claude Agent SDK more of a pre-configured
coding assistant you can restyle.

## Try it yourself

- Write a `system_prompt` that explicitly tells the agent it has access to tools,
  even when `tools=[]`, and see whether it hallucinates using one.
- Compare `claude-sonnet-5` against `claude-haiku-4-5` on a genuinely hard
  multi-step reasoning question instead of a trivial one, and check whether the
  cost gap is justified by a quality gap this time.
