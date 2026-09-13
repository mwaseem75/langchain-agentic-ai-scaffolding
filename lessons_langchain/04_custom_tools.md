# Lesson 4 — Custom Tools via `@tool`

**File:** `lessons_langchain/04_custom_tools.py`
**Run it:** `uv run lessons_langchain/04_custom_tools.py`
**Companion lesson:** the matching concept in the `claude-agentic-ai-scaffolding` repo
**Verified cost:** $0.0011 (worked on the first run)

## What this lesson is

Same scenario as the SDK curriculum's Lesson 4 — a `roll_dice` tool backed by real
`random.randint()` — but the LangChain path to get there is noticeably simpler in
two specific ways.

## Difference 1: no server-wrapping step

```python
@tool
def roll_dice(sides: int) -> str:
    """Roll an n-sided die and return the actual result."""
    result = random.randint(1, sides)
    call_log.append(f"rolled d{sides} -> {result}")
    return f"Rolled a d{sides}: {result}"

agent = create_agent(model=MODEL, tools=[roll_dice])
```

`@tool` alone turns the function into a `BaseTool`, handed directly to `tools=[]`.
There's no `create_sdk_mcp_server()`-equivalent step — LangChain's in-process
custom tools don't route through MCP at all; MCP only enters the picture for
*external* tool providers (Lesson 8).

## Difference 2: no naming-prefix gotcha

The SDK curriculum's Lesson 4 discovered — the hard way, via a failed first run —
that custom MCP tools are actually invoked as `mcp__<server>__<tool>`, not the bare
name the SDK's own docstring example showed. Here, no such surprise: the raw
`tool_use` dict shows the tool called by its **exact Python function name**:

```
{'input': {'sides': 6}, 'name': 'roll_dice', 'type': 'tool_use', ...}
```

Confirmed directly from output, not assumed.

## Results

```
[AIMessage] I'll roll two 6-sided dice for you. [tool_use: roll_dice(sides=6)] [tool_use: roll_dice(sides=6)]
[ToolMessage] 'Rolled a d6: 3'
[ToolMessage] 'Rolled a d6: 2'
[AIMessage] Sum: 3 + 2 = 5. Even or Odd: Odd.

[in-process call_log] ['rolled d6 -> 3', 'rolled d6 -> 2']
```

`call_log` — a plain Python list defined outside the tool — was mutated from
*inside* `roll_dice` and read back afterward, matching the `ToolMessage` results
exactly. Same in-process-state advantage as the SDK's custom tools: the tool runs
in this exact Python process, so it can touch your application's real objects
directly.

## Reference

| Step | claude-agent-sdk | LangChain |
|---|---|---|
| Define the tool | `@tool(name, description, input_schema)` | `@tool` (docstring becomes the description; type hints become the schema) |
| Wrap for the agent | `create_sdk_mcp_server(name, tools=[...])`, then `mcp_servers={...}` | Not needed — pass the decorated function straight into `tools=[...]` |
| Grant access | `allowed_tools=["mcp__<server>__<tool>"]` (prefixed!) | Tool is available the moment it's in `tools=[...]` — no separate allow-list |
| Runtime call name | `mcp__<server>__<tool>` | Exact function name |

## Key takeaway

LangChain's custom-tool path is simpler precisely because it has no MCP layer to
go through for in-process tools — `@tool` + `tools=[...]` is the entire mechanism.
The tradeoff shows up in Lesson 8: reaching an *external* process for tools does
require MCP, at which point LangChain needs an extra adapter package
(`langchain-mcp-adapters`) that the Claude Agent SDK doesn't, since MCP is native
to the SDK from the start.

## Try it yourself

- Add a docstring-only tool with no type hints and see how LangChain infers (or
  fails to infer) its schema.
- Make `roll_dice` raise an exception for `sides <= 0` and observe how the error
  surfaces in the `ToolMessage`.
