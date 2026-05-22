from __future__ import annotations

from pathlib import Path
from typing import Any

MAX_TOOL_OUTPUT = 50000
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _safe_path(raw_path: str) -> Path:
    target = (PROJECT_ROOT / raw_path).resolve()
    if not str(target).startswith(str(PROJECT_ROOT)):
        raise ValueError(f"Path traversal blocked: {raw_path}")
    return target


def _truncate(text: str, limit: int = MAX_TOOL_OUTPUT) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated, {len(text)} total chars]"


def tool_read_file(file_path: str) -> str:
    try:
        target = _safe_path(file_path)
        if not target.exists():
            return f"Error: File not found: {file_path}"
        if not target.is_file():
            return f"Error: Not a file: {file_path}"
        content = target.read_text(encoding="utf-8")
        return _truncate(content)
    except ValueError as exc:
        return str(exc)
    except Exception as exc:  # pragma: no cover - defensive fallback
        return f"Error: {exc}"


TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read file contents inside current project.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "File path relative to project root.",
                    }
                },
                "required": ["file_path"],
            },
        },
    }
]

TOOL_HANDLERS: dict[str, Any] = {
    "read_file": tool_read_file,
}

