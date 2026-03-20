"""
Layer 5 — Execution Layer
Uses Claude with tool use to execute the plan and generate the final response.
"""

from __future__ import annotations

import json
from typing import Any

import anthropic

from agent.layers.planning import Plan, PlanStep, StepStatus
from agent.tools.registry import ToolRegistry


class ExecutionLayer:
    """
    Drives Claude through the plan using the agentic tool-use loop.
    Handles tool calls, feeds results back, and produces the final answer.
    """

    MAX_TOOL_ITERATIONS = 10

    EXECUTION_SYSTEM = (
        "You are the Execution Core of a multi-layer AI agent. "
        "You have access to tools. Use them when needed to complete the task. "
        "Be thorough, accurate, and helpful. "
        "Reply in the same language as the user's input."
    )

    def __init__(self, client: anthropic.Anthropic, registry: ToolRegistry) -> None:
        self._client = client
        self._registry = registry

    def execute(
        self,
        user_input: str,
        plan: Plan,
        reasoning_context: str,
        memory_context: str,
        conversation_history: list[dict[str, str]],
    ) -> str:
        system_prompt = self._build_system_prompt(reasoning_context, memory_context, plan)
        messages = self._build_initial_messages(conversation_history, user_input, plan)
        tool_definitions = self._registry.get_tool_definitions()

        for iteration in range(self.MAX_TOOL_ITERATIONS):
            response = self._client.messages.create(
                model="claude-opus-4-6",
                max_tokens=8192,
                system=system_prompt,
                tools=tool_definitions if plan.strategy != "direct_answer" else [],
                messages=messages,
            )

            messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "end_turn":
                break

            if response.stop_reason == "tool_use":
                tool_results = self._handle_tool_calls(response.content, plan)
                messages.append({"role": "user", "content": tool_results})
                continue

            break

        return self._extract_final_text(response.content)

    def _build_system_prompt(
        self, reasoning_context: str, memory_context: str, plan: Plan
    ) -> str:
        return (
            f"{self.EXECUTION_SYSTEM}\n\n"
            f"{reasoning_context}\n\n"
            f"{memory_context}\n\n"
            f"{self._format_plan_guidance(plan)}"
        )

    def _format_plan_guidance(self, plan: Plan) -> str:
        if plan.strategy == "direct_answer":
            return "[Execution Mode: Direct Answer — no tools needed]"
        steps_text = "\n".join(
            f"  {i+1}. {s.description}" for i, s in enumerate(plan.steps)
        )
        return f"[Execution Plan]\nGoal: {plan.goal}\nSteps:\n{steps_text}"

    def _build_initial_messages(
        self,
        history: list[dict[str, str]],
        user_input: str,
        plan: Plan,
    ) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = list(history[:-1]) if len(history) > 1 else []
        messages.append({"role": "user", "content": user_input})
        return messages

    def _handle_tool_calls(
        self, content: list[Any], plan: Plan
    ) -> list[dict[str, Any]]:
        tool_results: list[dict[str, Any]] = []

        for block in content:
            if not hasattr(block, "type") or block.type != "tool_use":
                continue

            tool_name = block.name
            tool_input = block.input if isinstance(block.input, dict) else {}

            self._update_plan_step(plan, tool_name)

            result = self._registry.execute(tool_name, **tool_input)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result.output if result.success else f"Error: {result.error}",
                "is_error": not result.success,
            })

            if result.success:
                self._mark_step_done(plan, tool_name, result.output)

        return tool_results

    def _update_plan_step(self, plan: Plan, tool_name: str) -> None:
        for step in plan.steps:
            if step.tool == tool_name and step.status == StepStatus.PENDING:
                step.status = StepStatus.IN_PROGRESS
                break

    def _mark_step_done(self, plan: Plan, tool_name: str, result: str) -> None:
        for step in plan.steps:
            if step.tool == tool_name and step.status == StepStatus.IN_PROGRESS:
                step.status = StepStatus.DONE
                step.result = result[:200]
                break

    def _extract_final_text(self, content: list[Any]) -> str:
        text_parts = [
            block.text for block in content
            if hasattr(block, "type") and block.type == "text"
        ]
        return "\n".join(text_parts).strip() or "I was unable to generate a response."
