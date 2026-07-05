"""Lightweight execution tracer for agent/pipeline steps.

Independent of LangSmith — always works, adds negligible overhead, and gives
readable timing/step logs even when no external tracing backend is configured.
"""
from __future__ import annotations

import functools
import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Iterator

logger = logging.getLogger("revenue_guardian.trace")


@contextmanager
def trace_step(name: str, **context: Any) -> Iterator[None]:
    """Context manager that logs the duration and outcome of a step.

    Usage:
        with trace_step("analytics_agent", query=query):
            ...
    """
    start = time.perf_counter()
    logger.info("start step=%s context=%s", name, context)
    try:
        yield
    except Exception:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.exception("step=%s failed after %.1fms", name, elapsed_ms)
        raise
    else:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.info("step=%s completed in %.1fms", name, elapsed_ms)


def traced(name: str | None = None) -> Callable:
    """Decorator version of trace_step for sync or async functions."""

    def decorator(func: Callable) -> Callable:
        step_name = name or func.__name__

        if _is_coroutine_function(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                with trace_step(step_name):
                    return await func(*args, **kwargs)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            with trace_step(step_name):
                return func(*args, **kwargs)

        return sync_wrapper

    return decorator


def _is_coroutine_function(func: Callable) -> bool:
    import inspect

    return inspect.iscoroutinefunction(func)
