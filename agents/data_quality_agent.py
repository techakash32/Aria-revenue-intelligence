"""Data quality agent for MySQL revenue data.

Separate from the statistical anomaly agent (which only looks at whether
*aggregate daily revenue* moved too much). This agent looks at *row-level*
integrity problems in daily_sales that would otherwise silently corrupt the
analytics — negative values, price/quantity mismatches, future-dated rows,
missing names, invalid categories, and quantity outliers.

Every check is a single read-only SELECT, so it goes through the same
safety.sql_validator + safety.query_timeout path as everything else in
tools/sql_tool.py.
"""
from __future__ import annotations

from decimal import Decimal

import config
from tools.sql_tool import run_sql

DEFAULT_ALLOWED_CATEGORIES = ["Electronics", "Furniture", "Stationery", "Accessories"]
DEFAULT_OUTLIER_STD_DEV = 3.0
SAMPLE_LIMIT = 5

# ------------------------------------------------------------------
# Each check is: (issue_type, severity, human label, SQL)
# SQL always returns the offending rows (capped) so the report/alert
# can show real examples, not just a count.
# ------------------------------------------------------------------

def build_checks() -> list[dict]:
    allowed = config.get(
        "data_quality", "allowed_categories", default=DEFAULT_ALLOWED_CATEGORIES
    )
    allowed_sql_list = ", ".join(f"'{c}'" for c in allowed)
    std_dev_mult = config.get(
        "data_quality", "outlier_std_dev", default=DEFAULT_OUTLIER_STD_DEV
    )

    return [
        {
            "type": "negative_quantity",
            "severity": "critical",
            "label": "Negative quantity",
            "sql": f"""
                SELECT id, date, product_id, product_name, quantity
                FROM daily_sales
                WHERE quantity < 0
                LIMIT {SAMPLE_LIMIT}
            """,
        },
        {
            "type": "negative_unit_price",
            "severity": "critical",
            "label": "Negative unit price",
            "sql": f"""
                SELECT id, date, product_id, product_name, unit_price
                FROM daily_sales
                WHERE unit_price < 0
                LIMIT {SAMPLE_LIMIT}
            """,
        },
        {
            "type": "zero_unit_price",
            "severity": "medium",
            "label": "Zero unit price",
            "sql": f"""
                SELECT id, date, product_id, product_name, unit_price
                FROM daily_sales
                WHERE unit_price = 0
                LIMIT {SAMPLE_LIMIT}
            """,
        },
        {
            "type": "revenue_mismatch",
            "severity": "high",
            "label": "total_revenue does not equal quantity * unit_price",
            "sql": f"""
                SELECT id, date, product_id, product_name,
                       quantity, unit_price, total_revenue,
                       (quantity * unit_price) AS expected_revenue
                FROM daily_sales
                WHERE ABS(total_revenue - (quantity * unit_price)) > 0.01
                LIMIT {SAMPLE_LIMIT}
            """,
        },
        {
            "type": "future_dated_row",
            "severity": "high",
            "label": "Sale date is in the future",
            "sql": f"""
                SELECT id, date, product_id, product_name
                FROM daily_sales
                WHERE date > CURDATE()
                LIMIT {SAMPLE_LIMIT}
            """,
        },
        {
            "type": "missing_product_name",
            "severity": "low",
            "label": "product_name is NULL",
            "sql": f"""
                SELECT id, date, product_id
                FROM daily_sales
                WHERE product_name IS NULL
                LIMIT {SAMPLE_LIMIT}
            """,
        },
        {
            "type": "invalid_category",
            "severity": "low",
            "label": f"Category outside allowed list ({', '.join(allowed)})",
            "sql": f"""
                SELECT id, date, product_id, product_name, category
                FROM daily_sales
                WHERE category NOT IN ({allowed_sql_list})
                LIMIT {SAMPLE_LIMIT}
            """,
        },
        {
            "type": "inconsistent_product_mapping",
            "severity": "medium",
            "label": "Same product_id used with more than one product_name",
            "sql": f"""
                SELECT product_id, COUNT(DISTINCT product_name) AS name_variants
                FROM daily_sales
                GROUP BY product_id
                HAVING COUNT(DISTINCT product_name) > 1
                LIMIT {SAMPLE_LIMIT}
            """,
        },
        {
            "type": "quantity_outlier",
            "severity": "medium",
            "label": f"Quantity more than {std_dev_mult}x standard deviations from the mean",
            "sql": f"""
                SELECT id, date, product_id, product_name, quantity
                FROM daily_sales
                WHERE ABS(quantity - (SELECT AVG(quantity) FROM daily_sales))
                      > {std_dev_mult} * (SELECT STDDEV(quantity) FROM daily_sales)
                LIMIT {SAMPLE_LIMIT}
            """,
        },
    ]


async def run_data_quality_agent(state: dict) -> dict:
    """Run every check and attach a structured list of issues to state."""
    issues: list[dict] = []

    for check in build_checks():
        result = await run_sql(check["sql"])
        if not result.get("success"):
            # A failed check (e.g. STDDEV needs >=1 row) shouldn't crash the
            # pipeline — record it as its own low-severity issue and move on.
            issues.append(
                {
                    "type": check["type"],
                    "severity": "low",
                    "label": check["label"],
                    "count": 0,
                    "sample_rows": [],
                    "error": result.get("error"),
                }
            )
            continue

        rows = normalize_rows(result.get("data") or [])
        if rows:
            issues.append(
                {
                    "type": check["type"],
                    "severity": check["severity"],
                    "label": check["label"],
                    "count": len(rows),
                    "sample_rows": rows,
                }
            )

    state["data_quality_issues"] = issues
    state["data_quality_has_critical"] = any(
        issue["severity"] in ("critical", "high") for issue in issues
    )
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    return state


def normalize_rows(rows: list[dict]) -> list[dict]:
    return [{key: normalize_value(value) for key, value in row.items()} for row in rows]


def normalize_value(value):
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value
