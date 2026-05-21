"""
工具实现

每个工具使用 @register_tool 装饰器注册。
"""

import subprocess
from pathlib import Path

from .registry import register_tool

# ---------------------------------------------------------------------------
# 配置
# ---------------------------------------------------------------------------

MAX_TOOL_OUTPUT = 50000
WORKDIR = Path.cwd()


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


def safe_path(raw: str) -> Path:
    """防止路径穿越."""
    target = (WORKDIR / raw).resolve()
    if not str(target).startswith(str(WORKDIR)):
        raise ValueError(f"Path traversal blocked: {raw}")
    return target


def truncate(text: str, limit: int = MAX_TOOL_OUTPUT) -> str:
    """截断过长输出."""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated, {len(text)} total chars]"


# ---------------------------------------------------------------------------
# 工具实现
# ---------------------------------------------------------------------------


@register_tool("bash", {
    "description": (
        "Run a shell command and return its output. "
        "Use for system commands, git, package managers, etc."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute.",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds. Default 30.",
            },
        },
        "required": ["command"],
    },
})
def bash(command: str, timeout: int = 30) -> str:
    """执行 shell 命令."""
    dangerous = ["rm -rf /", "mkfs", "> /dev/sd", "dd if="]
    for pattern in dangerous:
        if pattern in command:
            return f"Error: Refused to run dangerous command containing '{pattern}'"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(WORKDIR),
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            output += ("\n--- stderr ---\n" + result.stderr) if output else result.stderr
        if result.returncode != 0:
            output += f"\n[exit code: {result.returncode}]"
        return truncate(output) if output else "[no output]"
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout}s"
    except Exception as exc:
        return f"Error: {exc}"


@register_tool("read_file", {
    "description": "Read the contents of a file.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file (relative to working directory).",
            },
        },
        "required": ["file_path"],
    },
})
def read_file(file_path: str) -> str:
    """读取文件内容."""
    try:
        target = safe_path(file_path)
        if not target.exists():
            return f"Error: File not found: {file_path}"
        if not target.is_file():
            return f"Error: Not a file: {file_path}"
        content = target.read_text(encoding="utf-8")
        return truncate(content)
    except ValueError as exc:
        return str(exc)
    except Exception as exc:
        return f"Error: {exc}"


@register_tool("write_file", {
    "description": (
        "Write content to a file. Creates parent directories if needed. "
        "Overwrites existing content."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file (relative to working directory).",
            },
            "content": {
                "type": "string",
                "description": "The content to write.",
            },
        },
        "required": ["file_path", "content"],
    },
})
def write_file(file_path: str, content: str) -> str:
    """写入文件."""
    try:
        target = safe_path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return f"Successfully wrote {len(content)} chars to {file_path}"
    except ValueError as exc:
        return str(exc)
    except Exception as exc:
        return f"Error: {exc}"


@register_tool("edit_file", {
    "description": (
        "Replace an exact string in a file with a new string. "
        "The old_string must appear exactly once in the file. "
        "Always read the file first to get the exact text to replace."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file (relative to working directory).",
            },
            "old_string": {
                "type": "string",
                "description": "The exact text to find and replace. Must be unique.",
            },
            "new_string": {
                "type": "string",
                "description": "The replacement text.",
            },
        },
        "required": ["file_path", "old_string", "new_string"],
    },
})
def edit_file(file_path: str, old_string: str, new_string: str) -> str:
    """精确替换文件内容."""
    try:
        target = safe_path(file_path)
        if not target.exists():
            return f"Error: File not found: {file_path}"

        content = target.read_text(encoding="utf-8")
        count = content.count(old_string)

        if count == 0:
            return "Error: old_string not found in file."
        if count > 1:
            return f"Error: old_string found {count} times. Must be unique."

        new_content = content.replace(old_string, new_string, 1)
        target.write_text(new_content, encoding="utf-8")
        return f"Successfully edited {file_path}"
    except ValueError as exc:
        return str(exc)
    except Exception as exc:
        return f"Error: {exc}"
