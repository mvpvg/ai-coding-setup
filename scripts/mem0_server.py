"""mem0 MCP server — mem0ai + OpenRouter via LiteLLM + FastEmbed (CPU-only).

Run via: uv run --with "mem0ai[mcp]" --with litellm --with fastembed scripts/mem0_server.py

Environment variables:
  OPENROUTER_API_KEY   Required. Your OpenRouter API key.
  MEM0_MODEL           LLM for fact extraction (default: openai/gpt-4o-mini)
  MEM0_EMBED_MODEL     FastEmbed model for vectors (default: BAAI/bge-small-en-v1.5, ~130 MB)
  MEM0_STORE_PATH      ChromaDB + history path (default: ~/.mem0)
  MEM0_USER_ID         User namespace for memories (default: default)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from mem0 import Memory

_OPENROUTER_BASE = "https://openrouter.ai/api/v1"

def _build_memory() -> Memory:
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    store_path = str(Path(os.environ.get("MEM0_STORE_PATH", "~/.mem0")).expanduser())

    config = {
        "llm": {
            "provider": "litellm",
            "config": {
                "model": os.environ.get("MEM0_MODEL", "openai/gpt-4o-mini"),
                "api_key": api_key,
                "api_base": _OPENROUTER_BASE,
            },
        },
        "embedder": {
            "provider": "fastembed",
            "config": {
                "model": os.environ.get("MEM0_EMBED_MODEL", "BAAI/bge-small-en-v1.5"),
            },
        },
        "vector_store": {
            "provider": "chroma",
            "config": {
                "collection_name": "mem0",
                "path": store_path,
            },
        },
        "history_db_path": str(Path(store_path) / "history.db"),
    }
    return Memory.from_config(config)


_USER_ID = os.environ.get("MEM0_USER_ID", "default")
_mem: Memory | None = None

def _get_memory() -> Memory:
    global _mem
    if _mem is None:
        _mem = _build_memory()
    return _mem


mcp = FastMCP("mem0")


@mcp.tool()
def health() -> str:
    """Check mem0 server status."""
    m = _get_memory()
    return f"mem0 MCP server running. User: {_USER_ID}. Store: {os.environ.get('MEM0_STORE_PATH', '~/.mem0')}"


@mcp.tool()
def memory_store(content: str, metadata: str = "") -> str:
    """Store a memory. Pass any relevant context as content."""
    m = _get_memory()
    meta = {}
    if metadata:
        import json
        try:
            meta = json.loads(metadata)
        except Exception:
            meta = {"raw": metadata}
    result = m.add(content, user_id=_USER_ID, metadata=meta)
    return f"Stored. IDs: {[r.get('id') for r in result.get('results', [])]}"


@mcp.tool()
def memory_search(query: str, limit: int = 5) -> str:
    """Search memories by semantic similarity."""
    m = _get_memory()
    results = m.search(query, user_id=_USER_ID, limit=limit)
    if not results.get("results"):
        return "No memories found."
    lines = []
    for r in results["results"]:
        score = r.get("score", "?")
        lines.append(f"[{score:.2f}] {r['memory']}")
    return "\n".join(lines)


@mcp.tool()
def memory_recall(limit: int = 10) -> str:
    """Recall recent memories."""
    m = _get_memory()
    results = m.get_all(user_id=_USER_ID, limit=limit)
    mems = results.get("results", [])
    if not mems:
        return "No memories yet."
    return "\n".join(f"- {r['memory']}" for r in mems)


@mcp.tool()
def memory_forget(memory_id: str) -> str:
    """Delete a specific memory by ID."""
    m = _get_memory()
    m.delete(memory_id=memory_id)
    return f"Deleted memory {memory_id}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
