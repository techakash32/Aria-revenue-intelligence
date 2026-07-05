import os

import mysql.connector
import pandas as pd
import streamlit as st


def get_readonly_config():
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": os.getenv("MYSQL_READONLY_USER"),
        "password": os.getenv("MYSQL_READONLY_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
    }


def get_app_db_config():
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
    }


def fetch_kpis_from_db(config):
    conn = mysql.connector.connect(**config)
    try:
        df = pd.read_sql_query("""
            SELECT
                COUNT(*) as total_transactions,
                COALESCE(SUM(total_revenue), 0) as total_revenue,
                COALESCE(AVG(total_revenue), 0) as avg_order_value,
                COUNT(DISTINCT product_id) as unique_products
            FROM daily_sales
            WHERE date IN (
                SELECT date
                FROM (
                    SELECT DISTINCT date
                    FROM daily_sales
                    ORDER BY date DESC
                    LIMIT 7
                ) latest_dates
            )
        """, conn)
        return normalize_kpis(df.iloc[0].to_dict())
    finally:
        conn.close()


def fetch_kpis():
    errors = []
    for config in (get_readonly_config(), get_app_db_config()):
        try:
            return fetch_kpis_from_db(config)
        except Exception as exc:
            errors.append(f"{config.get('user')}: {exc}")

    if errors:
        st.warning("MySQL is unavailable, showing bundled sample data.")
        with st.expander("Database details"):
            st.write("; ".join(errors))
    return fetch_sample_kpis()

def fetch_sample_kpis():
    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "sample_sales.csv",
    )
    df = pd.read_csv(sample_path)
    return {
        "total_transactions": int(len(df)),
        "total_revenue": float(df["total_revenue"].sum()),
        "avg_order_value": float(df["total_revenue"].mean()),
        "unique_products": int(df["product_id"].nunique()),
    }


def fetch_revenue_trend_from_db(config):
    conn = mysql.connector.connect(**config)
    try:
        return pd.read_sql_query("""
            SELECT date, SUM(total_revenue) as total_revenue
            FROM daily_sales
            WHERE date IN (
                SELECT date
                FROM (
                    SELECT DISTINCT date
                    FROM daily_sales
                    ORDER BY date DESC
                    LIMIT 7
                ) latest_dates
            )
            GROUP BY date
            ORDER BY date
        """, conn)
    finally:
        conn.close()


def fetch_revenue_trend():
    for config in (get_readonly_config(), get_app_db_config()):
        try:
            df = fetch_revenue_trend_from_db(config)
            if not df.empty:
                return df
        except Exception:
            continue

    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "sample_sales.csv",
    )
    df = pd.read_csv(sample_path)
    return df.groupby("date", as_index=False)["total_revenue"].sum()


def normalize_kpis(kpis):
    return {
        "total_transactions": int(kpis.get("total_transactions") or 0),
        "total_revenue": float(kpis.get("total_revenue") or 0),
        "avg_order_value": float(kpis.get("avg_order_value") or 0),
        "unique_products": int(kpis.get("unique_products") or 0),
    }


def render_kpi_cards():
    kpis = normalize_kpis(fetch_kpis())
    cols = st.columns(4)
    cols[0].metric("Transactions", f"{kpis.get('total_transactions', 0):,.0f}")
    cols[1].metric("Revenue", f"{kpis.get('total_revenue', 0):,.2f}")
    cols[2].metric("Avg Order Value", f"{kpis.get('avg_order_value', 0):,.2f}")
    cols[3].metric("Products", f"{kpis.get('unique_products', 0):,.0f}")

    df = fetch_revenue_trend()
    st.subheader("Revenue Trend")
    if df.empty:
        st.info("No revenue trend data found yet.")
        return
    st.line_chart(df.set_index("date")["total_revenue"])
