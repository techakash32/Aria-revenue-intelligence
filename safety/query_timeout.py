"""Cross-platform query execution timeout helpers."""
from __future__ import annotations

import concurrent.futures


class QueryTimeout(Exception):
    pass

def execute_with_timeout(cursor, query: str, timeout_seconds: int = 5):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_execute_and_fetch, cursor, query)
    try:
        return future.result(timeout=timeout_seconds)
    except concurrent.futures.TimeoutError as exc:
        future.cancel()
        raise QueryTimeout(f"Query exceeded {timeout_seconds} second limit") from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def _execute_and_fetch(cursor, query: str):
    cursor.execute(query)
    return cursor.fetchall()
