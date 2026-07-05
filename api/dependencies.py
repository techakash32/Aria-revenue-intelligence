"""Shared FastAPI dependencies: settings and DB config accessors.

Kept dependency-injection style (functions returning plain dicts/values) so
routes stay easy to test without a live database or network.
"""
from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    """Process-wide application settings, read once from environment."""

    def __init__(self) -> None:
        self.api_host: str = os.getenv("API_HOST", "0.0.0.0")
        self.api_port: int = int(os.getenv("API_PORT", "8000"))
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")
        self.max_iterations: int = int(os.getenv("MAX_ITERATIONS", "8"))
        self.query_timeout_seconds: int = int(os.getenv("QUERY_TIMEOUT_SECONDS", "5"))
        self.anomaly_threshold_percent: float = float(
            os.getenv("ANOMALY_THRESHOLD_PERCENT", "10.0")
        )
        self.chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

        self.mysql_host: str = os.getenv("MYSQL_HOST", "localhost")
        self.mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
        self.mysql_database: str = os.getenv("MYSQL_DATABASE", "revenue")

        self.groq_api_key: str | None = os.getenv("GROQ_API_KEY") or None
        self.whatsapp_configured: bool = bool(
            os.getenv("WHATSAPP_TOKEN") and os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        )


@lru_cache
def get_settings() -> Settings:
    """FastAPI dependency: `settings: Settings = Depends(get_settings)`."""
    return Settings()


def get_readonly_db_config() -> dict:
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": os.getenv("MYSQL_READONLY_USER"),
        "password": os.getenv("MYSQL_READONLY_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
    }


def get_app_db_config() -> dict:
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", 3306)),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_DATABASE"),
    }
