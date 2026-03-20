"""
MultiLayerAgent — Orchestrates all 6 cognitive layers.

Flow:
  Input → Perception → Memory → Reasoning → Planning → Execution → Reflection → Output
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import anthropic

from agent.layers.perception import PerceptionLayer, PerceptionResult
from agent.layers.memory import MemoryLayer
from agent.layers.reasoning import ReasoningLayer, ReasoningResult
from agent.layers.planning import PlanningLayer, Plan
from agent.layers.execution import ExecutionLayer
from agent.layers.reflection import ReflectionLayer, ReflectionResult
from agent.tools.registry import ToolRegistry
from agent.tools.builtins import register_builtin_tools


@dataclass
class AgentResponse:
    """Full structured response including all layer outputs."""
    user_input: str
    final_answer: str

    # Layer outputs (optional verbose data)
    perception: PerceptionResult | None = None
    reasoning: ReasoningResult | None = None
    plan: Plan | None = None
    reflection: ReflectionResult | None = None

    turn: int = 0
    verbose: bool = False

    def __str__(self) -> str:
        return self.final_answer


class MultiLayerAgent:
    """
    An AI agent with a six-layer cognitive architecture:

    1. Perception  — understand & classify input
    2. Memory      — recall context & facts
    3. Reasoning   — deep analysis with adaptive thinking
    4. Planning    — decompose task into steps
    5. Execution   — run tools and generate response
    6. Reflection  — evaluate quality & learn

    Usage:
        agent = MultiLayerAgent()
        response = agent.chat("What is 25 * 48?")
        print(response)
    """

    def __init__(
        self,
        api_key: str | None = None,
        verbose: bool = False,
        enable_reflection: bool = True,
    ) -> None:
        self._client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )
        self._verbose = verbose
        self._enable_reflection = enable_reflection
        self._turn = 0

        # Initialize layers
        self._perception = PerceptionLayer()
        self._memory = MemoryLayer()
        self._reasoning = ReasoningLayer(self._client)
        self._planning = PlanningLayer(self._client)
        self._registry = ToolRegistry()
        register_builtin_tools(self._registry)
        self._execution = ExecutionLayer(self._client, self._registry)
        self._reflection = ReflectionLayer(self._client)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def chat(self, user_input: str) -> AgentResponse:
        """Process a user message through all 6 layers and return the response."""
        self._turn += 1
        self._memory.remember(user_input, role="user", importance=1.0)

        # ── Layer 1: Perception ──────────────────────────────────────────
        perception_result = self._perception.process(user_input)
        perception_ctx = self._perception.to_prompt_context(perception_result)

        # ── Layer 2: Memory ──────────────────────────────────────────────
        memory_ctx = self._memory.build_context_block()

        # ── Layer 3: Reasoning ───────────────────────────────────────────
        reasoning_result = self._reasoning.analyze(
            perception_context=perception_ctx,
            memory_context=memory_ctx,
            user_input=user_input,
        )
        reasoning_ctx = self._reasoning.to_prompt_context(reasoning_result)

        # ── Layer 4: Planning ────────────────────────────────────────────
        plan = self._planning.create_plan(
            user_input=user_input,
            reasoning_context=reasoning_ctx,
            complexity=perception_result.complexity,
        )
        plan_ctx = self._planning.to_prompt_context(plan)

        # ── Layer 5: Execution ───────────────────────────────────────────
        conversation_history = self._memory.get_conversation_history()
        final_answer = self._execution.execute(
            user_input=user_input,
            plan=plan,
            reasoning_context=reasoning_ctx,
            memory_context=memory_ctx,
            conversation_history=conversation_history,
        )

        # Store assistant response
        self._memory.remember(final_answer, role="assistant", importance=0.9)

        # ── Layer 6: Reflection ──────────────────────────────────────────
        reflection_result: ReflectionResult | None = None
        if self._enable_reflection:
            reflection_result = self._reflection.evaluate(
                user_input=user_input,
                agent_response=final_answer,
                reasoning_insights=reasoning_result.key_insights,
                plan_summary=plan.summary(),
            )
            # Store learned facts in long-term memory
            for i, lesson in enumerate(reflection_result.lessons):
                self._memory.store_fact(
                    key=f"lesson_{self._turn}_{i}",
                    value=lesson,
                    source="reflection",
                )

        return AgentResponse(
            user_input=user_input,
            final_answer=final_answer,
            perception=perception_result,
            reasoning=reasoning_result,
            plan=plan,
            reflection=reflection_result,
            turn=self._turn,
            verbose=self._verbose,
        )

    def reset(self) -> None:
        """Clear all memory and reset turn counter."""
        self._memory.clear_all()
        self._turn = 0

    def get_memory_stats(self) -> dict[str, Any]:
        return self._memory.to_dict()

    def add_tool(
        self,
        name: str,
        handler: Any,
        description: str,
        schema: dict[str, Any] | None = None,
    ) -> None:
        """Register a custom tool with the agent."""
        self._registry.register(name, handler, description, schema)

    def list_tools(self) -> list[str]:
        return self._registry.list_tools()

    @property
    def turn(self) -> int:
        return self._turn
