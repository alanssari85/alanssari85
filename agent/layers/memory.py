"""
Layer 2 — Memory Layer
Manages short-term (conversation) and long-term (persistent facts) memory.
"""

from __future__ import annotations

import json
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryEntry:
    content: str
    role: str                       # "user" | "assistant" | "system"
    timestamp: float = field(default_factory=time.time)
    importance: float = 1.0        # 0.0–1.0; higher = retained longer
    tags: list[str] = field(default_factory=list)


@dataclass
class Fact:
    key: str
    value: Any
    confidence: float = 1.0
    source: str = "inferred"
    created_at: float = field(default_factory=time.time)


class MemoryLayer:
    """
    Two-tier memory:
      - Short-term: recent conversation turns (sliding window).
      - Long-term: persistent facts extracted from interactions.
    """

    SHORT_TERM_CAPACITY = 20  # max recent messages kept in context

    def __init__(self) -> None:
        self._short_term: deque[MemoryEntry] = deque(maxlen=self.SHORT_TERM_CAPACITY)
        self._long_term: dict[str, Fact] = {}
        self._episode_summary: str = ""

    # ------------------------------------------------------------------ #
    # Short-term
    # ------------------------------------------------------------------ #

    def remember(self, content: str, role: str, importance: float = 1.0,
                 tags: list[str] | None = None) -> None:
        entry = MemoryEntry(
            content=content,
            role=role,
            importance=importance,
            tags=tags or [],
        )
        self._short_term.append(entry)

    def get_conversation_history(self) -> list[dict[str, str]]:
        """Return messages in the format expected by the Anthropic API."""
        return [
            {"role": e.role, "content": e.content}
            for e in self._short_term
            if e.role in ("user", "assistant")
        ]

    def get_recent(self, n: int = 5) -> list[MemoryEntry]:
        entries = list(self._short_term)
        return entries[-n:]

    # ------------------------------------------------------------------ #
    # Long-term
    # ------------------------------------------------------------------ #

    def store_fact(self, key: str, value: Any, confidence: float = 1.0,
                   source: str = "inferred") -> None:
        self._long_term[key] = Fact(
            key=key,
            value=value,
            confidence=confidence,
            source=source,
        )

    def recall_fact(self, key: str) -> Fact | None:
        return self._long_term.get(key)

    def search_facts(self, query: str) -> list[Fact]:
        query_lower = query.lower()
        return [
            f for f in self._long_term.values()
            if query_lower in f.key.lower() or query_lower in str(f.value).lower()
        ]

    # ------------------------------------------------------------------ #
    # Episodic summary
    # ------------------------------------------------------------------ #

    def set_episode_summary(self, summary: str) -> None:
        self._episode_summary = summary

    def get_episode_summary(self) -> str:
        return self._episode_summary

    # ------------------------------------------------------------------ #
    # Context building
    # ------------------------------------------------------------------ #

    def build_context_block(self) -> str:
        lines: list[str] = ["[Memory Context]"]

        if self._episode_summary:
            lines.append(f"  Session summary: {self._episode_summary}")

        relevant_facts = list(self._long_term.values())
        if relevant_facts:
            lines.append("  Known facts:")
            for fact in relevant_facts[-5:]:  # last 5 facts
                lines.append(f"    - {fact.key}: {fact.value} (conf={fact.confidence:.1f})")

        recent = self.get_recent(3)
        if recent:
            lines.append("  Recent context:")
            for entry in recent:
                snippet = entry.content[:80].replace("\n", " ")
                lines.append(f"    [{entry.role}] {snippet}…")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "short_term_count": len(self._short_term),
            "long_term_facts": len(self._long_term),
            "episode_summary": self._episode_summary,
        }

    def clear_short_term(self) -> None:
        self._short_term.clear()

    def clear_all(self) -> None:
        self._short_term.clear()
        self._long_term.clear()
        self._episode_summary = ""
