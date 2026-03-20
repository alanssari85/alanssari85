"""
Tool Registry — registers and dispatches tools for the Execution Layer.
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ToolResult:
    success: bool
    output: str
    tool_name: str
    error: str = ""


ToolHandler = Callable[..., str]


class ToolRegistry:
    """Central registry for all agent tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolHandler] = {}
        self._descriptions: dict[str, str] = {}
        self._schemas: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        handler: ToolHandler,
        description: str,
        schema: dict[str, Any] | None = None,
    ) -> None:
        self._tools[name] = handler
        self._descriptions[name] = description
        self._schemas[name] = schema or {}

    def execute(self, name: str, **kwargs: Any) -> ToolResult:
        if name not in self._tools:
            return ToolResult(
                success=False,
                output="",
                tool_name=name,
                error=f"Tool '{name}' not found. Available: {list(self._tools.keys())}",
            )
        try:
            result = self._tools[name](**kwargs)
            return ToolResult(success=True, output=str(result), tool_name=name)
        except Exception as exc:
            return ToolResult(
                success=False,
                output="",
                tool_name=name,
                error=f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}",
            )

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        """Return Anthropic-compatible tool definitions."""
        definitions = []
        for name, description in self._descriptions.items():
            schema = self._schemas.get(name, {})
            definitions.append({
                "name": name,
                "description": description,
                "input_schema": schema or {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            })
        return definitions

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())

    def describe(self, name: str) -> str:
        return self._descriptions.get(name, "No description available.")
