from __future__ import annotations

from typing import Any

from .load_consult_skill_tool import TOOL_HANDLERS as LOAD_CONSULT_SKILL_TOOL_HANDLERS
from .load_consult_skill_tool import TOOLS as LOAD_CONSULT_SKILL_TOOLS
from .read_file_tool import TOOL_HANDLERS as READ_FILE_TOOL_HANDLERS
from .read_file_tool import TOOLS as READ_FILE_TOOLS
from .submit_consult_content_tool import TOOL_HANDLERS as SUBMIT_CONSULT_TOOL_HANDLERS
from .submit_consult_content_tool import TOOLS as SUBMIT_CONSULT_TOOLS
from .write_file_tool import TOOL_HANDLERS as WRITE_FILE_TOOL_HANDLERS
from .write_file_tool import TOOLS as WRITE_FILE_TOOLS
from .search_knowledge_tool import TOOL_HANDLERS as SEARCH_KNOWLEDGE_TOOL_HANDLERS
from .search_knowledge_tool import TOOLS as SEARCH_KNOWLEDGE_TOOLS

TOOLS: list[dict[str, Any]] = [
    *READ_FILE_TOOLS,
    *LOAD_CONSULT_SKILL_TOOLS,
    *SUBMIT_CONSULT_TOOLS,
    *SEARCH_KNOWLEDGE_TOOLS,
    *WRITE_FILE_TOOLS,
]
TOOL_HANDLERS: dict[str, Any] = {
    **READ_FILE_TOOL_HANDLERS,
    **LOAD_CONSULT_SKILL_TOOL_HANDLERS,
    **WRITE_FILE_TOOL_HANDLERS,
    **SUBMIT_CONSULT_TOOL_HANDLERS,
    **SEARCH_KNOWLEDGE_TOOL_HANDLERS,
}


def process_tool_call(tool_name: str, tool_input: dict[str, Any]) -> str:
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        return f"Error: Unknown tool '{tool_name}'"
    try:
        return handler(**tool_input)
    except TypeError as exc:
        return f"Error: Invalid arguments for {tool_name}: {exc}"
    except Exception as exc:  # pragma: no cover - defensive fallback
        return f"Error: {tool_name} failed: {exc}"

