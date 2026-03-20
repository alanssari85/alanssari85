"""
Layer 1 — Perception Layer
Parses and understands user input, extracts intent, entities, and context.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PerceptionResult:
    raw_input: str
    intent: str
    entities: dict[str, Any]
    complexity: str          # "simple" | "moderate" | "complex"
    requires_tools: bool
    language: str
    context_clues: list[str] = field(default_factory=list)


class PerceptionLayer:
    """
    Analyzes raw user input and extracts structured meaning.
    Determines complexity to inform downstream layers.
    """

    COMPLEXITY_KEYWORDS = {
        "simple": ["what is", "define", "tell me", "who is", "when did"],
        "moderate": ["how do", "explain", "compare", "list", "summarize"],
        "complex": [
            "design", "build", "create", "implement", "analyze deeply",
            "multi-step", "plan", "optimize", "debug", "refactor",
        ],
    }

    TOOL_TRIGGERS = [
        "calculate", "compute", "search", "find", "look up",
        "current", "today", "weather", "news", "latest",
        "count", "add", "subtract", "multiply", "divide",
        "read file", "write file", "execute", "run",
    ]

    def process(self, user_input: str) -> PerceptionResult:
        lowered = user_input.lower().strip()

        intent = self._extract_intent(lowered)
        entities = self._extract_entities(user_input)
        complexity = self._assess_complexity(lowered)
        requires_tools = self._needs_tools(lowered)
        language = self._detect_language(user_input)
        context_clues = self._gather_context_clues(user_input)

        return PerceptionResult(
            raw_input=user_input,
            intent=intent,
            entities=entities,
            complexity=complexity,
            requires_tools=requires_tools,
            language=language,
            context_clues=context_clues,
        )

    def _extract_intent(self, text: str) -> str:
        if any(w in text for w in ["?", "what", "how", "why", "when", "where", "who"]):
            return "question"
        if any(w in text for w in ["create", "build", "make", "generate", "write"]):
            return "creation"
        if any(w in text for w in ["fix", "debug", "solve", "correct", "repair"]):
            return "problem_solving"
        if any(w in text for w in ["explain", "describe", "tell", "clarify"]):
            return "explanation"
        if any(w in text for w in ["analyze", "evaluate", "review", "assess"]):
            return "analysis"
        return "general"

    def _extract_entities(self, text: str) -> dict[str, Any]:
        entities: dict[str, Any] = {}

        numbers = re.findall(r"\b\d+(?:\.\d+)?\b", text)
        if numbers:
            entities["numbers"] = [float(n) for n in numbers]

        quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', text)
        if quoted:
            entities["quoted_terms"] = [q[0] or q[1] for q in quoted]

        code_blocks = re.findall(r"```[\s\S]*?```|`[^`]+`", text)
        if code_blocks:
            entities["code_snippets"] = code_blocks

        return entities

    def _assess_complexity(self, text: str) -> str:
        for level in ("complex", "moderate", "simple"):
            if any(kw in text for kw in self.COMPLEXITY_KEYWORDS[level]):
                return level
        word_count = len(text.split())
        if word_count > 50:
            return "complex"
        if word_count > 20:
            return "moderate"
        return "simple"

    def _needs_tools(self, text: str) -> bool:
        return any(trigger in text for trigger in self.TOOL_TRIGGERS)

    def _detect_language(self, text: str) -> str:
        arabic_chars = sum(1 for c in text if "\u0600" <= c <= "\u06ff")
        if arabic_chars / max(len(text), 1) > 0.2:
            return "arabic"
        return "english"

    def _gather_context_clues(self, text: str) -> list[str]:
        clues: list[str] = []
        if any(w in text.lower() for w in ["step by step", "خطوة بخطوة"]):
            clues.append("wants_steps")
        if any(w in text.lower() for w in ["example", "مثال"]):
            clues.append("wants_example")
        if any(w in text.lower() for w in ["brief", "short", "quick", "بإختصار"]):
            clues.append("wants_brief")
        if any(w in text.lower() for w in ["detail", "thorough", "complete", "تفصيل"]):
            clues.append("wants_detail")
        return clues

    def to_prompt_context(self, result: PerceptionResult) -> str:
        return (
            f"[Perception Analysis]\n"
            f"  Intent: {result.intent}\n"
            f"  Complexity: {result.complexity}\n"
            f"  Language: {result.language}\n"
            f"  Requires tools: {result.requires_tools}\n"
            f"  Context clues: {', '.join(result.context_clues) or 'none'}\n"
            f"  Entities: {json.dumps(result.entities, ensure_ascii=False)}"
        )
