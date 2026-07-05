# observability/langsmith_setup.py
"""Optional LangSmith tracing bootstrap.

Tracing is only enabled when LANGCHAIN_API_KEY is present. Import of this
module must never raise, even with no key configured and no network access.
"""
import logging
import os

logger = logging.getLogger(__name__)


def init_langsmith():
    """Enable LangSmith tracing if an API key is configured.

    Returns a `langsmith.Client` on success, or None when tracing is
    disabled/unavailable (missing key, missing package, or network error).
    """
    api_key = os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        logger.info("LANGCHAIN_API_KEY not set; LangSmith tracing disabled.")
        return None

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ.setdefault("LANGCHAIN_PROJECT", "revenue-guardian")

    try:
        from langsmith import Client

        return Client(api_key=api_key)
    except Exception:
        logger.exception("Failed to initialize LangSmith client; continuing without tracing.")
        return None
