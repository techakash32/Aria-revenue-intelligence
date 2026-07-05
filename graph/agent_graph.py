"""LangGraph-compatible entry point.

The MVP runs a deterministic async pipeline first. This keeps the product usable
while the LangGraph supervisor can be expanded later without changing API calls.
"""
from __future__ import annotations

from pipelines.monitor_pipeline import run_monitor


async def run_agent_graph(query: str = "daily revenue monitor") -> dict:
    return await run_monitor(query=query)
