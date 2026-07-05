"""Loader for config/app_config.json.

Environment variables (see .env.example) still take precedence at the
call sites that read them directly (os.getenv) — this file backs the
non-secret, versionable defaults (thresholds, iteration limits, model
name) so they're reviewable in one place and in git history.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "app_config.json"


@lru_cache
def load_app_config() -> dict:
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get(*keys: str, default=None):
    """Dotted-path lookup, e.g. config.get('anomaly_detection', 'threshold_percent')."""
    node = load_app_config()
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node
