# Lesson 8 — External MCP Servers via `langchain-mcp-adapters`

**File:** `lessons_langchain/08_mcp_external_server.py`
**Run it:** `uv run lessons_langchain/08_mcp_external_server.py`
**Verified cost:** $0.002

## What this lesson is

`_mcp_word_count_server.py`, sitting right next to this script, is a standalone
MCP server that runs as its own OS process, talking to this lesson over stdio.
It's a deliberately tiny example — one tool, one job — so the interesting part
stays visible: connecting to something genuinely external, not another
in-process function call.

## A real dependency conflict, discovered by installing it

Adding `langchain-mcp-adapters` forces `mcp` to downgrade to 1.x in your virtual
environment — confirmed via
`importlib.metadata.metadata(...).get_all("Requires-Dist")`, which shows a hard
`mcp<2.0.0` constraint. That's a problem if you've ever written a server against
the mcp 2.x API, since it uses the mcp-2.x-only `mcp.server.mcpserver.MCPServer`
class, which won't exist once mcp is downgraded.

Fixed with a version-tolerant import in the server file:

```python
try:
    from mcp.server.mcpserver import MCPServer  # mcp >= 2.0
except ModuleNotFoundError:
    from mcp.server.fastmcp import FastMCP as MCPServer  # mcp < 2.0
```

Worth remembering: installing a new dependency can silently break unrelated,
already-working code elsewhere in the same project if two packages share a
transitive dependency with incompatible version requirements. Always re-check
adjacent code after a dependency install, not just the code you just wrote.

## Wiring up the client

```python
client = MultiServerMCPClient({
    "wordcount": {
        "transport": "stdio",
        "command": sys.executable,
        "args": [str(SERVER_SCRIPT)],   # ./_mcp_word_count_server.py, same folder
    }
})
tools = await client.get_tools()
```

## Two async surprises, found by actually running it

**Surprise 1 — `get_tools()` is async.** This is the first lesson in the folder
that needs `asyncio` at all, since opening a real stdio subprocess connection and
doing the MCP handshake is inherently asynchronous.

**Surprise 2 — the returned tools are *async-only*.** The first run failed with:

```
NotImplementedError: StructuredTool does not support sync invocation.
```

The MCP-adapter tool wrapper only implements `_arun`, not `_run`. `agent.invoke()`
(sync) cannot call it at all — the fix is `await agent.ainvoke(...)` instead,
inside one `asyncio.run(main())` covering the whole flow.

**A third thing tried and correctly rejected:** attempting
`async with MultiServerMCPClient(...) as client:` for cleaner resource teardown
raised the library's own explicit error:

```
NotImplementedError: As of langchain-mcp-adapters 0.1.0, MultiServerMCPClient
cannot be used as a context manager... Instead: client = MultiServerMCPClient(...);
tools = await client.get_tools()
```

— confirming the original (context-manager-free) approach was the library's
actual intended usage all along.

## Results — correct, with a known Windows quirk on exit

```
[lesson script] my own pid=13724
[loaded tools] ['count_words']
[ToolMessage] [{'text': '9 words (counted in external process pid=21772)', ...}]
[AIMessage] 'Word Count: 9 words. Process Information: PID 21772.'
[cost_usd~] 0.002130
```

**13724 vs. 21772** — two different numbers because they're two different
processes. That's the whole point of "external": the tool isn't a function call
inside your script, it's a conversation with something else entirely.

After every line above printed correctly, the process **segfaulted during
interpreter shutdown** (exit code 139). This is a known class of Windows-specific
`asyncio` + subprocess-transport teardown issue, not a logic bug — it happens only
during cleanup, after all real work and output is already complete. Worth
documenting rather than hiding, since it's the kind of thing that looks alarming
in a terminal until you understand where it's actually coming from.

## Reference

| | In-process tools (Lesson 4) | External MCP (this lesson) |
|---|---|---|
| Runs where | Same process as your script | A separate OS process |
| Wiring | `@tool`, straight into `tools=[...]` | `MultiServerMCPClient` + `get_tools()` |
| Sync-callable? | Yes | **No** — async-only; use `ainvoke()` |
| State sharing | Direct access to your app's Python objects | None — communicates only via tool call/result |

## Key takeaway

Reaching an external MCP server costs you something real: a whole extra
package, a hard version pin that can conflict with unrelated dependencies, and
a forced switch to fully async code even if the rest of your agent is
synchronous. That's a fair trade when you need real process isolation or a
tool written in another language — but it's not the default path, and you
should reach for it deliberately, not by habit.

## Try it yourself

- Point `command`/`args` at a real published MCP server (e.g. an `npx`-based one,
  if Node.js is available) instead of the local Python script.
- Try wrapping the whole `main()` body in a `try/finally` that explicitly cancels
  any lingering asyncio tasks before `asyncio.run()` returns, to see whether that
  avoids the shutdown segfault.
