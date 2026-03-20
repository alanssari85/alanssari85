"""
Layer 3 — Reasoning Layer
Uses Claude's adaptive thinking to perform deep analysis before responding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import anthropic


@dataclass
class ReasoningResult:
    thinking_content: str
    key_insights: list[str]
    approach: str
    confidence: float
    needs_more_info: bool
    sub_questions: list[str] = field(default_factory=list)


class ReasoningLayer:
    """
    Invokes Claude with adaptive thinking enabled to reason about the problem
    before committing to a plan. Returns structured insights.
    """

    REASONING_SYSTEM = (
        "You are the Reasoning Core of a multi-layer AI agent. "
        "Your job is to analyze the problem deeply, identify key considerations, "
        "surface hidden assumptions, spot potential issues, and determine the best approach. "
        "Think carefully before responding. "
        "Reply in the same language as the user's input."
    )

    def __init__(self, client: anthropic.Anthropic) -> None:
        self._client = client

    def analyze(
        self,
        perception_context: str,
        memory_context: str,
        user_input: str,
        planning_context: str = "",
    ) -> ReasoningResult:
        prompt = self._build_prompt(
            perception_context, memory_context, user_input, planning_context
        )

        response = self._client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            system=self.REASONING_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        thinking_text = ""
        analysis_text = ""
        for block in response.content:
            if block.type == "thinking":
                thinking_text = block.thinking
            elif block.type == "text":
                analysis_text = block.text

        return self._parse_analysis(thinking_text, analysis_text)

    def _build_prompt(
        self,
        perception_context: str,
        memory_context: str,
        user_input: str,
        planning_context: str,
    ) -> str:
        parts = [
            perception_context,
            memory_context,
        ]
        if planning_context:
            parts.append(planning_context)
        parts.append(f"\n[User Request]\n{user_input}")
        parts.append(
            "\n[Your Task]\n"
            "Analyze the request thoroughly. Provide:\n"
            "1. Key insights (list, 3-5 points)\n"
            "2. Recommended approach (one sentence)\n"
            "3. Confidence level (0.0-1.0)\n"
            "4. Whether more information is needed (yes/no)\n"
            "5. Any sub-questions that need answering first (list, optional)\n\n"
            "Format your response as:\n"
            "INSIGHTS:\n- ...\nAPPROACH: ...\nCONFIDENCE: 0.X\nNEEDS_MORE_INFO: yes/no\n"
            "SUB_QUESTIONS:\n- ... (optional)"
        )
        return "\n\n".join(parts)

    def _parse_analysis(self, thinking: str, text: str) -> ReasoningResult:
        lines = text.strip().split("\n")

        insights: list[str] = []
        approach = ""
        confidence = 0.8
        needs_more = False
        sub_questions: list[str] = []

        mode = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("INSIGHTS:"):
                mode = "insights"
            elif stripped.startswith("APPROACH:"):
                approach = stripped.replace("APPROACH:", "").strip()
                mode = None
            elif stripped.startswith("CONFIDENCE:"):
                try:
                    confidence = float(stripped.replace("CONFIDENCE:", "").strip())
                except ValueError:
                    confidence = 0.8
                mode = None
            elif stripped.startswith("NEEDS_MORE_INFO:"):
                val = stripped.replace("NEEDS_MORE_INFO:", "").strip().lower()
                needs_more = val in ("yes", "true", "1")
                mode = None
            elif stripped.startswith("SUB_QUESTIONS:"):
                mode = "sub_questions"
            elif mode == "insights" and stripped.startswith("-"):
                insights.append(stripped[1:].strip())
            elif mode == "sub_questions" and stripped.startswith("-"):
                sub_questions.append(stripped[1:].strip())

        if not approach:
            approach = "Provide a comprehensive, helpful response."

        return ReasoningResult(
            thinking_content=thinking,
            key_insights=insights,
            approach=approach,
            confidence=confidence,
            needs_more_info=needs_more,
            sub_questions=sub_questions,
        )

    def to_prompt_context(self, result: ReasoningResult) -> str:
        lines = ["[Reasoning Analysis]"]
        if result.key_insights:
            lines.append("  Key insights:")
            for insight in result.key_insights:
                lines.append(f"    - {insight}")
        lines.append(f"  Approach: {result.approach}")
        lines.append(f"  Confidence: {result.confidence:.1f}")
        if result.needs_more_info:
            lines.append("  Note: More information may be needed.")
        if result.sub_questions:
            lines.append("  Sub-questions to address:")
            for q in result.sub_questions:
                lines.append(f"    - {q}")
        return "\n".join(lines)
