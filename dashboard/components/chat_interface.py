"""Dashboard chat and manual monitor controls."""
from __future__ import annotations

import asyncio

import streamlit as st

from pipelines.monitor_pipeline import run_monitor
from tools.llm_tool import answer_business_question


def render_chat_interface() -> None:
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

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
                reply = result.get("final_report") or "Monitor completed."
                render_monitor_result(result)
            else:
                reply = run_async(answer_business_question(prompt))
            st.write(reply)

    st.session_state.chat_messages.append({"role": "assistant", "content": reply})


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
    keywords = ("revenue", "sales", "anomaly", "drop", "spike", "monitor")
    return any(keyword in lowered for keyword in keywords)


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
