"""ARIA Revenue Guardian Streamlit dashboard."""
from __future__ import annotations

import asyncio
import os
import sys

import streamlit as st
from dotenv import load_dotenv

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dashboard.components.chat_interface import render_chat_interface, render_monitor_button
from dashboard.components.decision_log import render_decision_log
from dashboard.components.kpi_cards import render_kpi_cards


def main() -> None:
    load_dotenv()

    st.set_page_config(
        page_title="ARIA - Revenue Guardian",
        page_icon=":bar_chart:",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    with st.sidebar:
        st.title("ARIA")
        st.caption("Revenue Guardian")
        st.divider()
        page = st.radio("Navigate", ["Dashboard", "Chat", "Decision Log"], index=0)
        st.divider()
        st.caption("FastAPI, Streamlit, MySQL, Groq")

    if page == "Dashboard":
        st.title("Revenue Dashboard")
        st.caption("Live revenue monitoring, anomaly detection, and alert status.")
        st.divider()
        render_monitor_button()
        st.divider()
        render_kpi_cards()
    elif page == "Chat":
        st.title("ARIA Chat")
        st.caption("Ask questions or run the revenue monitor in natural language.")
        st.divider()
        render_chat_interface()
    else:
        st.title("Agent Decision Log")
        st.caption("Recent automated decisions and confidence scores.")
        st.divider()
        render_decision_log(limit=20)


if __name__ == "__main__":
    main()
