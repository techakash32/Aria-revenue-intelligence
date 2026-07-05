from tools.whatsapp_tool import send_whatsapp_alert


async def run_action_agent(state: dict) -> dict:
    anomalies = state.get("anomalies_found", [])
    quality_issues = state.get("data_quality_issues", [])
    critical_quality_issues = [
        issue for issue in quality_issues if issue["severity"] in ("critical", "high")
    ]

    has_stat_anomaly = bool(anomalies)
    has_critical_quality_issue = bool(critical_quality_issues)

    if not has_stat_anomaly and not has_critical_quality_issue:
        state["action_taken"] = "none"
        state["alert_sent"] = False
        state["alert_skip_reason"] = "No anomalies or critical data quality issues"
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        return state

    anomaly = anomalies[0] if anomalies else None
    confidence = anomaly.get("confidence", 0.0) if anomaly else 0.0
    severity = anomaly.get("severity", "low") if anomaly else "low"

    # Alert if EITHER the statistical anomaly clears the bar OR there's a
    # critical/high data quality issue — a negative-revenue row or a
    # future-dated sale is worth flagging even if daily totals look normal.
    should_alert = (severity in ("medium", "high") and confidence >= 0.5) or has_critical_quality_issue

    if should_alert:
        message = build_alert_message(anomaly, quality_issues)
        result = await send_whatsapp_alert(message)
        state["alert_sent"] = result.get("sent", False)
        state["action_taken"] = "whatsapp_alert" if result.get("sent") else "whatsapp_failed"
        state["alert_message_id"] = result.get("message_id")
        state["alert_skip_reason"] = result.get("reason") if not result.get("sent") else None
    else:
        state["alert_sent"] = False
        state["action_taken"] = "alert_skipped"
        state["alert_skip_reason"] = f"Confidence {confidence} or severity {severity} too low"

    state["iteration_count"] = state.get("iteration_count", 0) + 1
    return state


def build_alert_message(anomaly: dict | None, quality_issues: list[dict]) -> str:
    lines = ["🚨 *Revenue Guardian Alert*"]

    if anomaly and anomaly.get("is_anomaly"):
        lines.append("")
        lines.append("*Revenue Anomaly*")
        lines.append(f"• Change: {anomaly.get('change_percent', 0):+.1f}%")
        lines.append(f"• Severity: {anomaly.get('severity', 'unknown').upper()}")
        lines.append(f"• Date: {anomaly.get('latest_date', 'N/A')}")
        lines.append(f"• Reason: {anomaly.get('reason', 'N/A')}")

    if quality_issues:
        lines.append("")
        lines.append(f"*Data Quality Issues ({len(quality_issues)})*")
        for issue in sorted(quality_issues, key=lambda i: severity_rank(i["severity"])):
            lines.append(
                f"• [{issue['severity'].upper()}] {issue['label']} "
                f"— {issue['count']} row(s)"
            )

    return "\n".join(lines)


def severity_rank(severity: str) -> int:
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return order.get(severity, 4)