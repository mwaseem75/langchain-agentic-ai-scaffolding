"""
Lesson 8 - external MCP servers via langchain-mcp-adapters.

Talks to _mcp_word_count_server.py, a standalone script in this same
folder that runs as its own OS process over stdio. Its own PID-reporting
trick proves the point: the tool runs in a genuinely separate OS process
from this script, not inside it.

This is the first lesson in this folder that needs asyncio, and it turns
out to need it more thoroughly than expected: MultiServerMCPClient.get_tools()
is async (it opens a real stdio subprocess connection and does the MCP
handshake), AND the tool objects it returns are async-only - they implement
only `_arun`, not `_run`. Calling agent.invoke() (sync) on an agent holding
one of these tools fails with "StructuredTool does not support sync
invocation" - confirmed by actually hitting that error on the first run.
The fix is agent.ainvoke() instead, inside one asyncio.run() covering the
whole flow.

Known Windows-specific quirk, observed directly: after all output prints
correctly (including the final cost line), the process segfaults during
interpreter shutdown (exit code 139) while asyncio tears down the stdio
subprocess transport. This does not affect correctness - it happens after
every real piece of work is already done and printed - and is a known
class of issue with asyncio subprocess transports on Windows at
interpreter exit, not a bug in this script's logic. Documented rather than
suppressed, the same way the SDK curriculum documented its Windows
UTF-8-console crash.

Real dependency quirk worth knowing: the `mcp` package's server class was
renamed between major versions - `mcp.server.fastmcp.FastMCP` (mcp 1.x)
became `mcp.server.mcpserver.MCPServer` (mcp 2.x), and
langchain-mcp-adapters hard-requires mcp<2.0.0. _mcp_word_count_server.py
handles this with a version-tolerant try/except import so it works
whichever major version ends up installed.
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

MODEL = "claude-haiku-4-5"
SERVER_SCRIPT = Path(__file__).resolve().parent / "_mcp_word_count_server.py"

print(f"[lesson script] my own pid={os.getpid()}")


async def main():
    # NOT `async with MultiServerMCPClient(...)` - the library explicitly raises
    # NotImplementedError if you try that; get_tools() manages its own session.
    client = MultiServerMCPClient(
        {
            "wordcount": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [str(SERVER_SCRIPT)],
            }
        }
    )
    tools = await client.get_tools()
    print(f"[loaded tools] {[t.name for t in tools]}")

    agent = create_agent(model=MODEL, tools=tools)
    result = await agent.ainvoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": (
                        "Use the count_words tool to count the words in this sentence: "
                        "'The quick brown fox jumps over the lazy dog.' "
                        "Report the count and any process info it gives you."
                    ),
                }
            ]
        }
    )
    for msg in result["messages"]:
        print(f"[{type(msg).__name__}] {msg.content!r}")

    cost = 0.0
    for msg in result["messages"]:
        usage = getattr(msg, "usage_metadata", None)
        if usage:
            cost += usage.get("input_tokens", 0) * 1.0 / 1_000_000
            cost += usage.get("output_tokens", 0) * 5.0 / 1_000_000
    print(f"\n[cost_usd~] {cost:.6f}")


if __name__ == "__main__":
    asyncio.run(main())
