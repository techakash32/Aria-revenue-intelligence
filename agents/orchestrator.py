"""Simple orchestrator used by the MVP pipeline."""
from __future__ import annotations

from agents.action_agent import run_action_agent
from agents.analytics_agent import run_analytics_agent
from agents.anomaly_agent import run_anomaly_agent
from agents.data_quality_agent import run_data_quality_agent


async def run_orchestrator(state: dict) -> dict:
    state = await run_analytics_agent(state)
    if state.get("error"):
        return state

    # Data quality runs independently of the statistical anomaly check —
    # a row-level problem (negative price, future date, etc.) doesn't stop
    # the revenue-trend analysis, but it does get surfaced in the report
    # and can trigger its own alert via the action agent.
    state = await run_data_quality_agent(state)

    state = await run_anomaly_agent(state)
    if state.get("error"):
        return state

    return await run_action_agent(state)
