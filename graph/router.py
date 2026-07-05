"""Supervisor routing helpers for future LangGraph expansion."""
from __future__ import annotations

from graph.state import AgentState


def route_next(state: AgentState) -> str:
    if state["iteration_count"] >= state["max_iterations"]:
        return "report_agent"
    if state["task_complete"] or state.get("error"):
        return "report_agent"
    if state["raw_data"] is None:
        return "analytics_agent"
    if state["anomalies_found"] is None:
        return "anomaly_agent"
    if state["action_taken"] is None:
        return "action_agent"
    return "report_agent"
