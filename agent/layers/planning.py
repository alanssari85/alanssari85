"""
Layer 4 — Planning Layer
Decomposes complex tasks into ordered, executable steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import anthropic


class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    index: int
    description: str
    tool: str | None = None          # tool name if this step requires a tool
    tool_args: dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: str = ""
    depends_on: list[int] = field(default_factory=list)  # indices of prerequisite steps


@dataclass
class Plan:
    goal: str
    steps: list[PlanStep]
    strategy: str
    estimated_turns: int = 1

    @property
    def is_complete(self) -> bool:
        return all(s.status in (StepStatus.DONE, StepStatus.SKIPPED) for s in self.steps)

    @property
    def next_step(self) -> PlanStep | None:
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                deps_met = all(
                    self.steps[d].status == StepStatus.DONE
                    for d in step.depends_on
                    if d < len(self.steps)
                )
                if deps_met:
                    return step
        return None

    def mark_step(self, index: int, status: StepStatus, result: str = "") -> None:
        if 0 <= index < len(self.steps):
            self.steps[index].status = status
            self.steps[index].result = result

    def summary(self) -> str:
        done = sum(1 for s in self.steps if s.status == StepStatus.DONE)
        total = len(self.steps)
        return f"Plan: {self.goal} | Progress: {done}/{total} steps"


class PlanningLayer:
    """
    Converts a reasoning result into a concrete, step-by-step execution plan.
    For simple requests, produces a single-step plan.
    For complex ones, decomposes into ordered, dependency-aware steps.
    """

    PLANNING_SYSTEM = (
        "You are the Planning Core of a multi-layer AI agent. "
        "Given an analysis of a user request, produce a concrete, ordered execution plan. "
        "Each step must be clear and actionable. "
        "Identify which steps need external tools and which can be answered directly. "
        "Reply in the same language as the user's input."
    )

    AVAILABLE_TOOLS = ["calculator", "web_search", "file_reader", "code_executor", "none"]

    def __init__(self, client: anthropic.Anthropic) -> None:
        self._client = client

    def create_plan(
        self,
        user_input: str,
        reasoning_context: str,
        complexity: str,
    ) -> Plan:
        if complexity == "simple":
            return Plan(
                goal=user_input[:100],
                steps=[PlanStep(index=0, description="Answer directly", tool=None)],
                strategy="direct_answer",
                estimated_turns=1,
            )

        prompt = self._build_prompt(user_input, reasoning_context)
        response = self._client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            system=self.PLANNING_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )

        text = next(
            (b.text for b in response.content if b.type == "text"), ""
        )
        return self._parse_plan(user_input, text)

    def _build_prompt(self, user_input: str, reasoning_context: str) -> str:
        tools_str = ", ".join(self.AVAILABLE_TOOLS)
        return (
            f"{reasoning_context}\n\n"
            f"[User Request]\n{user_input}\n\n"
            f"[Available Tools]\n{tools_str}\n\n"
            "[Your Task]\n"
            "Create an execution plan. Format exactly as:\n"
            "GOAL: <one-line goal>\n"
            "STRATEGY: <brief strategy description>\n"
            "STEPS:\n"
            "1. [tool:none] <description>\n"
            "2. [tool:calculator] <description>\n"
            "...\n"
            "ESTIMATED_TURNS: <number>"
        )

    def _parse_plan(self, user_input: str, text: str) -> Plan:
        lines = text.strip().split("\n")
        goal = user_input[:100]
        strategy = "multi_step"
        steps: list[PlanStep] = []
        estimated_turns = 2
        in_steps = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("GOAL:"):
                goal = stripped.replace("GOAL:", "").strip()
            elif stripped.startswith("STRATEGY:"):
                strategy = stripped.replace("STRATEGY:", "").strip()
            elif stripped.startswith("ESTIMATED_TURNS:"):
                try:
                    estimated_turns = int(stripped.replace("ESTIMATED_TURNS:", "").strip())
                except ValueError:
                    estimated_turns = 2
            elif stripped.startswith("STEPS:"):
                in_steps = True
            elif in_steps and stripped and stripped[0].isdigit():
                step = self._parse_step_line(stripped, len(steps))
                if step:
                    steps.append(step)

        if not steps:
            steps = [PlanStep(index=0, description="Answer the request directly", tool=None)]

        return Plan(
            goal=goal,
            steps=steps,
            strategy=strategy,
            estimated_turns=estimated_turns,
        )

    def _parse_step_line(self, line: str, index: int) -> PlanStep | None:
        # Format: "1. [tool:calculator] description"
        import re
        match = re.match(r"\d+\.\s*(?:\[tool:(\w+)\])?\s*(.+)", line)
        if not match:
            return None
        tool_name = match.group(1)
        description = match.group(2).strip()
        tool = tool_name if tool_name and tool_name != "none" else None
        return PlanStep(index=index, description=description, tool=tool)

    def to_prompt_context(self, plan: Plan) -> str:
        lines = [f"[Execution Plan]", f"  Goal: {plan.goal}", f"  Strategy: {plan.strategy}"]
        for step in plan.steps:
            tool_info = f" (tool: {step.tool})" if step.tool else ""
            status_icon = {"pending": "⏳", "in_progress": "🔄", "done": "✅",
                           "failed": "❌", "skipped": "⏭"}.get(step.status.value, "?")
            lines.append(f"  {status_icon} Step {step.index + 1}: {step.description}{tool_info}")
        return "\n".join(lines)
