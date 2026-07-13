"""Revenue monitoring pipeline."""
from __future__ import annotations

from agents.orchestrator import run_orchestrator
from observability.decision_logger import log_decision


async def run_monitor(query: str = "daily revenue monitor") -> dict:
    state = initial_state(query)
    try:
        state = await run_orchestrator(state)
    except Exception as exc:
        state["error"] = str(exc)
        state["task_complete"] = True
    state["final_report"] = build_final_report(state)

    log_decision(
        agent_id="monitor_pipeline",
        input_data={"query": query},
        output_data=state,
        confidence=float(state.get("confidence_score") or 0),
        action_taken=state.get("action_taken") or "none",
    )
    return state


def initial_state(query: str) -> dict:
    return {
        "query": query,
        "raw_data": None,
        "anomalies_found": None,
        "data_quality_issues": None,
        "data_quality_has_critical": False,
        "confidence_score": 0.0,
        "action_taken": None,
        "action_result": None,
        "iteration_count": 0,
        "max_iterations": 8,
        "task_complete": False,
        "final_report": None,
        "error": None,
    }


def build_final_report(state: dict) -> str:
    if state.get("error"):
        return f"Monitor failed: {state['error']}"

    summary = (state.get("raw_data") or {}).get("summary") or {}
    anomalies = state.get("anomalies_found") or []
    quality_issues = state.get("data_quality_issues") or []
    action = format_action(state.get("action_taken"))

    lines = []

    if anomalies:
        anomaly = anomalies[0]
        lines.append(
            f"{format_label(anomaly.get('type'))} detected on {anomaly.get('latest_date')}: "
            f"{anomaly.get('change_percent')}% change versus baseline."
        )
    else:
        lines.append(
            f"No revenue anomaly detected. Latest revenue is {summary.get('latest_revenue', 0):,.2f} "
            f"against baseline {summary.get('baseline_revenue', 0):,.2f}."
        )

    if quality_issues:
        lines.append(f"Data quality issues found ({len(quality_issues)}):")
        for issue in quality_issues:
            lines.append(f"  - [{issue['severity'].upper()}] {issue['label']}: {issue['count']} row(s)")
    else:
        lines.append("No data quality issues found.")

    lines.append(f"Action: {action}.")
    return "\n".join(lines)


def format_label(value: str | None) -> str:
    return (value or "unknown").replace("_", " ").title()


def format_action(value: str | None) -> str:
    return format_label(value or "none")
