"""
Layer 6 — Reflection Layer
Evaluates the quality of the response and updates long-term memory with lessons.
"""

from __future__ import annotations

from dataclasses import dataclass

import anthropic


@dataclass
class ReflectionResult:
    quality_score: float       # 0.0–1.0
    completeness: float        # did we fully answer the request?
    accuracy_check: str        # brief note on potential inaccuracies
    lessons: list[str]         # facts to store in long-term memory
    improvement_notes: str     # what could be done better
    should_follow_up: bool     # should agent ask a clarifying question?
    follow_up_question: str    # the follow-up if needed


class ReflectionLayer:
    """
    After generating a response, this layer reviews it against the original
    request and reasoning to extract lessons and judge quality.
    """

    REFLECTION_SYSTEM = (
        "You are the Reflection Core of a multi-layer AI agent. "
        "Your role is to critically evaluate agent responses for quality, "
        "completeness, and accuracy, then extract learnable lessons. "
        "Be concise and honest. Reply in the same language as the user's input."
    )

    def __init__(self, client: anthropic.Anthropic) -> None:
        self._client = client

    def evaluate(
        self,
        user_input: str,
        agent_response: str,
        reasoning_insights: list[str],
        plan_summary: str,
    ) -> ReflectionResult:
        prompt = self._build_prompt(
            user_input, agent_response, reasoning_insights, plan_summary
        )
        response = self._client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            system=self.REFLECTION_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = next((b.text for b in response.content if b.type == "text"), "")
        return self._parse_reflection(text)

    def _build_prompt(
        self,
        user_input: str,
        agent_response: str,
        reasoning_insights: list[str],
        plan_summary: str,
    ) -> str:
        insights_text = "\n".join(f"- {i}" for i in reasoning_insights) or "none"
        return (
            f"[Original Request]\n{user_input}\n\n"
            f"[Reasoning Insights]\n{insights_text}\n\n"
            f"[Execution Plan]\n{plan_summary}\n\n"
            f"[Agent Response]\n{agent_response}\n\n"
            "[Your Task]\n"
            "Evaluate the response. Format exactly as:\n"
            "QUALITY: 0.X\n"
            "COMPLETENESS: 0.X\n"
            "ACCURACY_CHECK: <brief note or 'seems accurate'>\n"
            "LESSONS:\n- <lesson>\n"
            "IMPROVEMENT: <note or 'none'>\n"
            "FOLLOW_UP: yes/no\n"
            "FOLLOW_UP_QUESTION: <question if yes, else empty>"
        )

    def _parse_reflection(self, text: str) -> ReflectionResult:
        lines = text.strip().split("\n")

        quality = 0.8
        completeness = 0.8
        accuracy_check = "seems accurate"
        lessons: list[str] = []
        improvement = "none"
        follow_up = False
        follow_up_q = ""
        mode = None

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("QUALITY:"):
                try:
                    quality = float(stripped.replace("QUALITY:", "").strip())
                except ValueError:
                    pass
            elif stripped.startswith("COMPLETENESS:"):
                try:
                    completeness = float(stripped.replace("COMPLETENESS:", "").strip())
                except ValueError:
                    pass
            elif stripped.startswith("ACCURACY_CHECK:"):
                accuracy_check = stripped.replace("ACCURACY_CHECK:", "").strip()
                mode = None
            elif stripped.startswith("LESSONS:"):
                mode = "lessons"
            elif stripped.startswith("IMPROVEMENT:"):
                improvement = stripped.replace("IMPROVEMENT:", "").strip()
                mode = None
            elif stripped.startswith("FOLLOW_UP:"):
                val = stripped.replace("FOLLOW_UP:", "").strip().lower()
                follow_up = val in ("yes", "true")
                mode = None
            elif stripped.startswith("FOLLOW_UP_QUESTION:"):
                follow_up_q = stripped.replace("FOLLOW_UP_QUESTION:", "").strip()
                mode = None
            elif mode == "lessons" and stripped.startswith("-"):
                lessons.append(stripped[1:].strip())

        return ReflectionResult(
            quality_score=quality,
            completeness=completeness,
            accuracy_check=accuracy_check,
            lessons=lessons,
            improvement_notes=improvement,
            should_follow_up=follow_up,
            follow_up_question=follow_up_q,
        )

    def format_summary(self, result: ReflectionResult) -> str:
        quality_bar = "█" * int(result.quality_score * 10) + "░" * (10 - int(result.quality_score * 10))
        return (
            f"[Reflection Summary]\n"
            f"  Quality:      [{quality_bar}] {result.quality_score:.1f}\n"
            f"  Completeness: {result.completeness:.1f}\n"
            f"  Accuracy:     {result.accuracy_check}\n"
            f"  Lessons:      {len(result.lessons)} learned\n"
            f"  Improvement:  {result.improvement_notes}"
        )
