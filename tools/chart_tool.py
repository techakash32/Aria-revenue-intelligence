"""Chart generation for revenue trends and anomaly highlighting.

Uses matplotlib with the non-interactive 'Agg' backend so it works in
headless environments (API server, CI, Docker) with no display. Returns
base64-encoded PNG bytes so the API/dashboard can embed charts without
touching the filesystem.
"""
from __future__ import annotations

import base64
import io
from datetime import date, datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def render_revenue_trend_chart(
    daily_rows: list[dict],
    anomaly: dict | None = None,
    title: str = "Revenue Trend",
) -> str:
    """Render a daily revenue line chart and return it as a base64 PNG string.

    Args:
        daily_rows: list of {"date": ..., "daily_revenue": ...} ordered by date ascending.
        anomaly: optional anomaly dict (from agents.anomaly_agent) — if it flags
            an anomaly, the latest point is highlighted in red.
        title: chart title.

    Returns:
        Base64-encoded PNG image data (no data: URI prefix).
    """
    dates = [_as_date_label(row.get("date")) for row in daily_rows]
    values = [float(row.get("daily_revenue") or 0) for row in daily_rows]

    fig, ax = plt.subplots(figsize=(8, 4), dpi=120)
    ax.plot(dates, values, marker="o", linewidth=2, color="#2563eb", label="Daily revenue")

    if anomaly and anomaly.get("is_anomaly") and values:
        ax.scatter(
            [dates[-1]],
            [values[-1]],
            color="#dc2626",
            s=90,
            zorder=5,
            label=f"Anomaly ({anomaly.get('type', 'unknown')})",
        )

    ax.set_title(title)
    ax.set_ylabel("Revenue")
    ax.set_xlabel("Date")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(alpha=0.3)
    ax.legend(loc="best")
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def render_category_breakdown_chart(
    category_rows: list[dict],
    title: str = "Revenue by Category",
) -> str:
    """Render a horizontal bar chart of revenue by category as a base64 PNG string."""
    labels = [str(row.get("category")) for row in category_rows]
    values = [float(row.get("revenue") or 0) for row in category_rows]

    fig, ax = plt.subplots(figsize=(8, 4), dpi=120)
    ax.barh(labels, values, color="#16a34a")
    ax.set_title(title)
    ax.set_xlabel("Revenue")
    ax.invert_yaxis()
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def _as_date_label(value) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)
