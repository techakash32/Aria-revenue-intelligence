"""Statistical anomaly detection (no external LLM)."""
from __future__ import annotations

import os

import config

DEFAULT_THRESHOLD_PERCENT = 10.0  # Lowered for MVP testing

async def run_anomaly_agent(state: dict) -> dict:
    raw_data = state.get("raw_data") or {}
    summary = raw_data.get("summary") or {}
    change_percent = float(summary.get("change_percent") or 0)
    # Precedence: explicit state override > env var > config/app_config.json > hardcoded default.
    config_default = config.get(
        "anomaly_detection", "threshold_percent", default=DEFAULT_THRESHOLD_PERCENT
    )
    threshold = float(
        state.get("anomaly_threshold_percent")
        or os.getenv("ANOMALY_THRESHOLD_PERCENT", config_default)
    )

    anomaly = build_anomaly(summary, change_percent, threshold)
    # No LLM call – just attach a static interpretation
    anomaly["interpretation"] = interpret_anomaly_static(anomaly)

    state["anomalies_found"] = [anomaly] if anomaly["is_anomaly"] else []
    state["confidence_score"] = anomaly["confidence"]
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    return state


def build_anomaly(summary: dict, change_percent: float, threshold: float) -> dict:
    days_analyzed = int(summary.get("days_analyzed") or 0)
    if days_analyzed < 3:
        return {
            "is_anomaly": False,
            "type": "insufficient_data",
            "severity": "low",
            "confidence": 0.0,          # No alert should be sent
            "change_percent": change_percent,
            "reason": f"Only {days_analyzed} days of data – need at least 3.",
        }

    is_anomaly = abs(change_percent) >= threshold
    if change_percent <= -threshold:
        anomaly_type = "revenue_drop"
        severity = "high" if abs(change_percent) >= 50 else "medium"
        reason = (
            f"Revenue dropped {abs(change_percent):.1f}% versus the recent baseline "
            f"on {summary.get('latest_date')}."
        )
    elif change_percent >= threshold:
        anomaly_type = "revenue_spike"
        severity = "medium"
        reason = (
            f"Revenue increased {change_percent:.1f}% versus the recent baseline "
            f"on {summary.get('latest_date')}."
        )
    else:
        anomaly_type = "normal"
        severity = "none"
        reason = (
            f"Revenue changed {change_percent:.1f}% versus the recent baseline, "
            "inside the configured threshold."
        )

    # Confidence: higher if change is larger, but cap at 0.95
    confidence = min(0.95, 0.55 + abs(change_percent) / 100) if is_anomaly else 0.0
    # Ensure confidence > 0.5 for medium/high severity to trigger alert
    if severity in ("medium", "high") and confidence < 0.5:
        confidence = 0.5

    return {
        "is_anomaly": is_anomaly,
        "type": anomaly_type,
        "severity": severity,
        "confidence": round(confidence, 2),
        "change_percent": round(change_percent, 2),
        "latest_revenue": summary.get("latest_revenue", 0),
        "baseline_revenue": summary.get("baseline_revenue", 0),
        "latest_date": summary.get("latest_date"),
        "reason": reason,
    }


def interpret_anomaly_static(anomaly: dict) -> str:
    """Provide a simple explanation without calling an LLM."""
    if not anomaly["is_anomaly"]:
        return "No significant anomaly detected."
    if anomaly["type"] == "revenue_drop":
        return f"Revenue dropped {abs(anomaly['change_percent']):.1f}% – possible causes: seasonality, marketing pause, or technical issue."
    if anomaly["type"] == "revenue_spike":
        return f"Revenue spiked {anomaly['change_percent']:.1f}% – likely due to a promotion or external event."
    return "Anomaly detected but type unknown."
