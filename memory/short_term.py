"""In-process short-term memory: a bounded rolling buffer of recent turns.

Used to give the chat/dashboard a small conversational window without a
database round-trip. Not persisted — resets on process restart. Long-term,
durable memory lives in observability.decision_logger (MySQL) and
memory.semantic_store (Chroma).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Deque, Iterable


@dataclass
class Turn:
    role: str  # "user" | "assistant"
    content: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ShortTermMemory:
    """Fixed-size FIFO buffer of conversation turns."""

    def __init__(self, max_turns: int = 20) -> None:
        self.max_turns = max_turns
        self._buffer: Deque[Turn] = deque(maxlen=max_turns)

    def add(self, role: str, content: str) -> None:
        self._buffer.append(Turn(role=role, content=content))

    def add_user(self, content: str) -> None:
        self.add("user", content)

    def add_assistant(self, content: str) -> None:
        self.add("assistant", content)

    def recent(self, n: int | None = None) -> list[Turn]:
        items = list(self._buffer)
        return items[-n:] if n else items

    def as_context(self, n: int | None = None) -> str:
        """Render recent turns as plain text, newest last — handy as LLM context."""
        return "\n".join(f"{turn.role}: {turn.content}" for turn in self.recent(n))

    def clear(self) -> None:
        self._buffer.clear()

    def __len__(self) -> int:
        return len(self._buffer)

    def __iter__(self) -> Iterable[Turn]:
        return iter(self._buffer)
