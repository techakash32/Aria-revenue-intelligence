"""Dashboard chat and manual monitor controls."""
from __future__ import annotations

import asyncio

import streamlit as st

from pipelines.monitor_pipeline import run_monitor
from tools.llm_tool import answer_business_question


def render_chat_interface() -> None:
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "last_monitor_result" not in st.session_state:
        st.session_state.last_monitor_result = None

    st.subheader("Ask ARIA")
    for message in st.session_state.chat_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    prompt = st.chat_input("Ask about revenue, sales, anomalies, or monitoring")
    if not prompt:
        return

    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            if should_run_monitor(prompt):
                result = run_async(run_monitor(query=prompt))
                st.session_state.last_monitor_result = result  # cache for follow-ups
                reply = result.get("final_report") or "Monitor completed."
                render_monitor_result(result)
            else:
                # FIX: pass last monitor result as context so ARIA can answer
                # follow-up questions ("why is anomaly -48.76%?") instead of
                # calling the LLM with an empty context every time.
                context = build_chat_context(st.session_state.last_monitor_result)
                reply = run_async(answer_business_question(prompt, context))
        st.write(reply)

    st.session_state.chat_messages.append({"role": "assistant", "content": reply})


def build_chat_context(result: dict | None) -> dict:
    """Turn the last monitor run into a compact context dict for the LLM."""
    if not result:
        return {}

    raw_data = result.get("raw_data") or {}
    summary = raw_data.get("summary") or {}
    anomalies = result.get("anomalies_found") or []
    anomaly = anomalies[0] if anomalies else {}

    return {
        "latest_revenue": summary.get("latest_revenue"),
        "baseline_revenue": summary.get("baseline_revenue"),
        "change_percent": summary.get("change_percent"),
        "latest_date": summary.get("latest_date"),
        "days_analyzed": summary.get("days_analyzed"),
        "anomaly_type": anomaly.get("type"),
        "anomaly_severity": anomaly.get("severity"),
        "anomaly_reason": anomaly.get("reason"),
        "anomaly_confidence": anomaly.get("confidence"),
        "data_quality_issues": result.get("data_quality_issues", []),
        "action_taken": result.get("action_taken"),
    }


def render_monitor_button() -> None:
    left, right = st.columns([1, 3])
    with left:
        run_clicked = st.button("Run Monitor Now", use_container_width=True)
    with right:
        # UPDATED: Telegram → WhatsApp
        st.caption("Checks latest MySQL sales, detects anomalies, logs the decision, and sends WhatsApp alert if needed.")

    if run_clicked:
        with st.spinner("Running revenue monitor..."):
            result = run_async(run_monitor())
        st.session_state.last_monitor_result = result  # cache for follow-ups
        if result.get("error"):
            st.error(result.get("final_report") or result["error"])
        else:
            st.success(result.get("final_report") or "Monitor completed.")
        render_monitor_result(result)


def render_monitor_result(result: dict) -> None:
    raw_data = result.get("raw_data") or {}
    summary = raw_data.get("summary") or {}
    anomalies = result.get("anomalies_found") or []
    anomaly = anomalies[0] if anomalies else {}

    cols = st.columns(4)
    cols[0].metric("Latest Revenue", format_money(summary.get("latest_revenue")))
    cols[1].metric("Baseline", format_money(summary.get("baseline_revenue")))
    cols[2].metric("Change", f"{float(summary.get('change_percent') or 0):.2f}%")
    cols[3].metric("Confidence", f"{float(result.get('confidence_score') or 0):.2f}")

    if anomaly:
        st.info(anomaly.get("interpretation") or anomaly.get("reason") or "Anomaly detected.")

    with st.expander("Run details"):
        # UPDATED: show WhatsApp alert status, not Telegram
        whatsapp_status = {
            "sent": result.get("alert_sent", False),
            "message_id": result.get("alert_message_id"),
            "skip_reason": result.get("alert_skip_reason"),
        }
        details = {
            "action": format_label(result.get("action_taken")),
            "whatsapp": whatsapp_status,
            "anomalies": anomalies,
            "category_revenue": raw_data.get("category_revenue", []),
            "top_products": raw_data.get("top_products", []),
        }
        st.json(details)


def should_run_monitor(message: str) -> bool:
    lowered = message.lower()
    # FIX: only re-run the full SQL monitor pipeline on an explicit action
    # word. Topic words alone ("revenue", "drop", "anomaly") used to
    # re-trigger a fresh run even for follow-up questions like "what's the
    # baseline revenue?" — those should answer from cached context instead.
    action_words = ("run", "check", "trigger", "refresh", "recheck", "rerun", "re-run")
    return any(word in lowered for word in action_words)


def run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def format_money(value) -> str:
    return f"{float(value or 0):,.2f}"


def format_label(value: str | None) -> str:
    return (value or "none").replace("_", " ").title()