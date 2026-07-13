"""Analytics agent for MySQL revenue data."""
from __future__ import annotations

from decimal import Decimal

from tools.sql_tool import run_sql

# ============================================================
# FIXED: Using your actual column names:
#   - total_revenue (not revenue)
#   - product_name (already exists, no alias needed)
#   - table = daily_sales
# ============================================================

DAILY_REVENUE_SQL = """
SELECT date, SUM(total_revenue) as daily_revenue
FROM daily_sales
WHERE date <= CURDATE()
  AND date IN (
    SELECT date FROM (
        SELECT DISTINCT date FROM daily_sales
        WHERE date <= CURDATE()
        ORDER BY date DESC LIMIT 14
    ) latest_dates
)
GROUP BY date
ORDER BY date ASC
"""

CATEGORY_REVENUE_SQL = """
SELECT category, SUM(total_revenue) as revenue
FROM daily_sales
GROUP BY category
ORDER BY revenue DESC
LIMIT 5
"""

PRODUCT_REVENUE_SQL = """
SELECT product_name, SUM(total_revenue) as revenue
FROM daily_sales
GROUP BY product_name
ORDER BY revenue DESC
LIMIT 5
"""


async def run_analytics_agent(state: dict) -> dict:
    daily_result = await run_sql(DAILY_REVENUE_SQL)
    category_result = await run_sql(CATEGORY_REVENUE_SQL)
    product_result = await run_sql(PRODUCT_REVENUE_SQL)

    if not daily_result.get("success"):
        state["error"] = daily_result.get("error", "Analytics query failed")
        return state

    daily_rows = normalize_rows(daily_result.get("data") or [])
    category_rows = normalize_rows(category_result.get("data") or [])
    product_rows = normalize_rows(product_result.get("data") or [])
    summary = build_summary(daily_rows)

    state["raw_data"] = {
        "daily_revenue": daily_rows,
        "category_revenue": category_rows,
        "top_products": product_rows,
        "summary": summary,
    }
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    return state


def build_summary(daily_rows: list[dict]) -> dict:
    if not daily_rows:
        return {
            "latest_date": None,
            "latest_revenue": 0.0,
            "baseline_revenue": 0.0,
            "change_percent": 0.0,
            "days_analyzed": 0,
        }

    latest = daily_rows[-1]
    history = daily_rows[-8:-1] if len(daily_rows) > 1 else []
    latest_revenue = float(latest.get("daily_revenue") or 0)
    baseline = (
        sum(float(row.get("daily_revenue") or 0) for row in history) / len(history)
        if history
        else latest_revenue
    )
    change_percent = ((latest_revenue - baseline) / baseline * 100) if baseline else 0.0

    return {
        "latest_date": latest.get("date"),
        "latest_revenue": latest_revenue,
        "baseline_revenue": baseline,
        "change_percent": change_percent,
        "days_analyzed": len(daily_rows),
    }


def normalize_rows(rows: list[dict]) -> list[dict]:
    return [{key: normalize_value(value) for key, value in row.items()} for row in rows]


def normalize_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
