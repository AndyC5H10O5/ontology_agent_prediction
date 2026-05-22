from __future__ import annotations

from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _safe_path(raw_path: str) -> Path:
    target = (PROJECT_ROOT / raw_path).resolve()
    if not str(target).startswith(str(PROJECT_ROOT)):
        raise ValueError(f"Path traversal blocked: {raw_path}")
    return target


def tool_write_file(file_path: str, content: str) -> str:
    try:
        target = _safe_path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} chars to {file_path}"
    except ValueError as exc:
        return str(exc)
    except Exception as exc:  # pragma: no cover - defensive fallback
        return f"Error: {exc}"


TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": (
                "Write UTF-8 text to a file under the project root. "
                "For generated personal treatment plans, use path under treatment_plan/, e.g. treatment_plan/plan_2026-04-11.md"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Relative path from project root; treatment plans should be under treatment_plan/.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full content to write into the file.",
                    },
                },
                "required": ["file_path", "content"],
            },
        },
    }
]

TOOL_HANDLERS: dict[str, Any] = {
    "write_file": tool_write_file,
}

