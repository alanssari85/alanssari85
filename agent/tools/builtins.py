"""
Built-in tools: calculator, web_search (simulated), file_reader, code_executor.
"""

from __future__ import annotations

import ast
import math
import os
import textwrap
from typing import Any

from agent.tools.registry import ToolRegistry


# ------------------------------------------------------------------ #
# Tool implementations
# ------------------------------------------------------------------ #

def _calculator(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    SAFE_NAMES: dict[str, Any] = {
        k: getattr(math, k) for k in dir(math) if not k.startswith("_")
    }
    SAFE_NAMES.update({"abs": abs, "round": round, "min": min, "max": max})

    try:
        # Parse to AST to block dangerous code
        tree = ast.parse(expression, mode="eval")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and not isinstance(node.func, ast.Name):
                raise ValueError("Only math function calls are allowed.")
        result = eval(compile(tree, "<string>", "eval"), {"__builtins__": {}}, SAFE_NAMES)
        return f"Result: {result}"
    except Exception as exc:
        return f"Calculation error: {exc}"


def _web_search(query: str) -> str:
    """
    Simulated web search — in production, replace with a real search API.
    Returns a placeholder result to demonstrate the tool-use flow.
    """
    return (
        f"[Simulated Search Results for: '{query}']\n"
        "Note: This is a demo. In production, integrate a real search API "
        "(e.g., Brave Search, Tavily, SerpAPI) here.\n"
        "Top result: The query was received and would return relevant web results."
    )


def _file_reader(file_path: str, max_chars: int = 2000) -> str:
    """Read a file from disk (restricted to current working directory)."""
    # Security: only allow reading from cwd or subdirectories
    abs_path = os.path.realpath(file_path)
    cwd = os.path.realpath(os.getcwd())
    if not abs_path.startswith(cwd):
        return f"Access denied: '{file_path}' is outside the working directory."
    if not os.path.exists(abs_path):
        return f"File not found: '{file_path}'"
    try:
        with open(abs_path, encoding="utf-8", errors="replace") as f:
            content = f.read(max_chars)
        if len(content) == max_chars:
            content += "\n[... truncated ...]"
        return f"File: {file_path}\n---\n{content}"
    except Exception as exc:
        return f"Error reading file: {exc}"


def _code_executor(code: str, language: str = "python") -> str:
    """
    Execute Python code in a restricted namespace.
    WARNING: This is a simplified demo executor. In production, use a
    proper sandbox (e.g., Docker, subprocess with resource limits).
    """
    if language.lower() != "python":
        return f"Only Python is supported in this demo. Got: {language}"

    ALLOWED_BUILTINS = {
        "print": print, "range": range, "len": len, "str": str,
        "int": int, "float": float, "list": list, "dict": dict,
        "set": set, "tuple": tuple, "bool": bool, "type": type,
        "enumerate": enumerate, "zip": zip, "map": map, "filter": filter,
        "sorted": sorted, "sum": sum, "min": min, "max": max, "abs": abs,
        "round": round, "repr": repr, "isinstance": isinstance,
    }

    import io
    import contextlib

    stdout_buffer = io.StringIO()
    namespace: dict[str, Any] = {"__builtins__": ALLOWED_BUILTINS}

    try:
        with contextlib.redirect_stdout(stdout_buffer):
            exec(textwrap.dedent(code), namespace)  # noqa: S102
        output = stdout_buffer.getvalue()
        return f"Execution successful.\nOutput:\n{output}" if output else "Execution successful. (no output)"
    except Exception as exc:
        return f"Execution error: {type(exc).__name__}: {exc}"


# ------------------------------------------------------------------ #
# Registration
# ------------------------------------------------------------------ #

def register_builtin_tools(registry: ToolRegistry) -> None:
    registry.register(
        name="calculator",
        handler=_calculator,
        description="Evaluate mathematical expressions. Supports standard math functions.",
        schema={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression to evaluate, e.g. '2 + 2' or 'sqrt(16)'",
                }
            },
            "required": ["expression"],
        },
    )

    registry.register(
        name="web_search",
        handler=_web_search,
        description="Search the web for information. Returns top results.",
        schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                }
            },
            "required": ["query"],
        },
    )

    registry.register(
        name="file_reader",
        handler=_file_reader,
        description="Read the contents of a text file (must be in the working directory).",
        schema={
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Relative path to the file to read",
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Maximum characters to return (default 2000)",
                },
            },
            "required": ["file_path"],
        },
    )

    registry.register(
        name="code_executor",
        handler=_code_executor,
        description="Execute Python code and return the output.",
        schema={
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute",
                },
                "language": {
                    "type": "string",
                    "description": "Programming language (currently only 'python')",
                },
            },
            "required": ["code"],
        },
    )
