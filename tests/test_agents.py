"""Unit tests for the anomaly and action agents. Fully mocked — no MySQL/WhatsApp needed."""
from __future__ import annotations

import pytest

from agents.action_agent import run_action_agent
from agents.anomaly_agent import build_anomaly, run_anomaly_agent


def make_summary(change_percent: float, days_analyzed: int = 8) -> dict:
    return {
        "latest_date": "2025-03-10",
        "latest_revenue": 1000.0,
        "baseline_revenue": 900.0,
        "change_percent": change_percent,
        "days_analyzed": days_analyzed,
    }


def test_build_anomaly_flags_drop_as_high_severity():
    anomaly = build_anomaly(make_summary(-60), change_percent=-60, threshold=10.0)
    assert anomaly["is_anomaly"] is True
    assert anomaly["type"] == "revenue_drop"
    assert anomaly["severity"] == "high"


def test_build_anomaly_flags_spike_as_medium_severity():
    anomaly = build_anomaly(make_summary(25), change_percent=25, threshold=10.0)
    assert anomaly["is_anomaly"] is True
    assert anomaly["type"] == "revenue_spike"
    assert anomaly["severity"] == "medium"


def test_build_anomaly_inside_threshold_is_not_an_anomaly():
    anomaly = build_anomaly(make_summary(3), change_percent=3, threshold=10.0)
    assert anomaly["is_anomaly"] is False
    assert anomaly["type"] == "normal"


def test_build_anomaly_insufficient_data_never_alerts():
    anomaly = build_anomaly(make_summary(80, days_analyzed=1), change_percent=80, threshold=10.0)
    assert anomaly["is_anomaly"] is False
    assert anomaly["type"] == "insufficient_data"
    assert anomaly["confidence"] == 0.0


@pytest.mark.asyncio
async def test_run_anomaly_agent_sets_state_fields():
    state = {"raw_data": {"summary": make_summary(-30)}}
    result = await run_anomaly_agent(state)
    assert result["anomalies_found"], "expected an anomaly to be recorded"
    assert result["confidence_score"] > 0
    assert result["iteration_count"] == 1


@pytest.mark.asyncio
async def test_action_agent_skips_when_no_anomalies():
    state = {"anomalies_found": []}
    result = await run_action_agent(state)
    assert result["action_taken"] == "none"
    assert result["alert_sent"] is False


@pytest.mark.asyncio
async def test_action_agent_sends_alert_for_high_severity(monkeypatch):
    async def fake_send_whatsapp_alert(message: str) -> dict:
        assert "Revenue Anomaly" in message
        return {"sent": True, "message_id": "wamid.TEST123"}

    monkeypatch.setattr("agents.action_agent.send_whatsapp_alert", fake_send_whatsapp_alert)

    state = {
        "anomalies_found": [
            {
                "is_anomaly": True,
                "type": "revenue_drop",
                "severity": "high",
                "confidence": 0.9,
                "change_percent": -55.0,
                "latest_date": "2025-03-10",
                "reason": "Revenue dropped sharply.",
            }
        ]
    }
    result = await run_action_agent(state)
    assert result["action_taken"] == "whatsapp_alert"
    assert result["alert_sent"] is True
    assert result["alert_message_id"] == "wamid.TEST123"


@pytest.mark.asyncio
async def test_action_agent_skips_low_confidence_alerts():
    state = {
        "anomalies_found": [
            {
                "is_anomaly": True,
                "type": "revenue_drop",
                "severity": "medium",
                "confidence": 0.1,
                "change_percent": -12.0,
                "latest_date": "2025-03-10",
                "reason": "Small dip.",
            }
        ]
    }
    result = await run_action_agent(state)
    assert result["action_taken"] == "alert_skipped"
    assert result["alert_sent"] is False
