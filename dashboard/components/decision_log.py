"""Readable decision-log view for agent runs."""
from __future__ import annotations

import json
import os

import mysql.connector
import pandas as pd
import streamlit as st


def get_db_config():
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
    }


def fetch_decisions(limit=20):
    limit = max(1, min(int(limit), 100))
    conn = None
    try:
        conn = mysql.connector.connect(**get_db_config())
        return pd.read_sql_query(
            """
            SELECT agent_id, timestamp, confidence, action_taken,
                   input, output
            FROM agent_decisions
            ORDER BY timestamp DESC
            LIMIT %s
            """,
            conn,
            params=(limit,),
        )
    except Exception as exc:
        st.warning(f"Decision log is not available yet: {exc}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()


def render_decision_log(limit=20):
    df = fetch_decisions(limit=limit)
    if df.empty:
        st.info("No decisions found yet. Run the monitor once to create the first decision.")
        return

    parsed_rows = [summarize_row(row) for _, row in df.iterrows()]
    summary_df = pd.DataFrame(
        [
            {
                "Time": row["timestamp"],
                "Agent": row["agent_id"],
                "Confidence": row["confidence"],
                "Action": row["action_taken"],
                "Result": row["result"],
            }
            for row in parsed_rows
        ]
    )

    st.dataframe(summary_df, use_container_width=True, hide_index=True)
    st.divider()

    for row in parsed_rows:
        title = f"{row['timestamp']} - {format_label(row['action_taken'])}"
        with st.expander(title):
            cols = st.columns(4)
            cols[0].metric("Confidence", f"{float(row['confidence'] or 0):.2f}")
            cols[1].metric("Action", format_label(row["action_taken"]))
            cols[2].metric("Latest Revenue", format_money(row["latest_revenue"]))
            cols[3].metric("Change", f"{float(row['change_percent'] or 0):.2f}%")

            if row["final_report"]:
                st.write(row["final_report"])

            details = {
                "input": row["input"],
                "summary": row["summary"],
                "anomalies": row["anomalies"],
                "telegram": row["telegram"],
            }
            st.json(details)


def summarize_row(row) -> dict:
    input_data = parse_json(row.get("input"))
    output_data = parse_json(row.get("output"))
    summary = (output_data.get("raw_data") or {}).get("summary") or {}
    anomalies = output_data.get("anomalies_found") or []
    anomaly = anomalies[0] if anomalies else {}

    return {
        "timestamp": row.get("timestamp"),
        "agent_id": row.get("agent_id"),
        "confidence": row.get("confidence") or 0,
        "action_taken": row.get("action_taken") or "none",
        "input": input_data,
        "summary": summary,
        "anomalies": anomalies,
        "telegram": output_data.get("action_result"),
        "final_report": output_data.get("final_report"),
        "latest_revenue": summary.get("latest_revenue", 0),
        "change_percent": anomaly.get("change_percent", summary.get("change_percent", 0)),
        "result": output_data.get("final_report") or format_label(row.get("action_taken")),
    }


def parse_json(value):
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return {"raw": str(value)}


def format_money(value) -> str:
    return f"{float(value or 0):,.2f}"


def format_label(value: str | None) -> str:
    return (value or "none").replace("_", " ").title()
