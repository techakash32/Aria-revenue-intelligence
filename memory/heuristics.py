# memory/heuristics.py

RECOVERY_HEURISTICS = [
    {
        "pattern": "revenue_drop_friday_evening",
        "threshold": -15,       # % drop
        "action": "send_weekend_promo_alert",
        "reasoning": "Friday evening drops often recover with weekend promotions"
    },
    {
        "pattern": "revenue_drop_monday_morning",
        "threshold": -20,
        "action": "check_payment_gateway_status",
        "reasoning": "Monday morning drops frequently caused by payment gateway issues"
    },
    {
        "pattern": "sudden_spike_above_50_percent",
        "threshold": 50,
        "action": "verify_data_integrity",
        "reasoning": "Spikes this large are often data pipeline errors, not real sales"
    }
]

def match_heuristic(pattern_type: str, value: float) -> dict | None:
    for h in RECOVERY_HEURISTICS:
        if h["pattern"] == pattern_type:
            if abs(value) >= abs(h["threshold"]):
                return h
    return None
