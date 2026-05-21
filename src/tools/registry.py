"""
工具注册中心

提供工具注册和调度机制。
"""

from typing import Any, Callable


class ToolRegistry:
    """工具注册中心."""

    def __init__(self):
        self._tools: list[dict] = []
        self._handlers: dict[str, Callable] = {}

    def register(self, name: str, schema: dict, handler: Callable) -> None:
        """注册工具."""
        self._tools.append({"name": name, **schema})
        self._handlers[name] = handler

    def get_handler(self, name: str) -> Callable | None:
        """获取工具处理函数."""
        return self._handlers.get(name)

    def get_tools(self) -> list[dict]:
        """获取所有工具 schema (用于 API)."""
        return self._tools.copy()

    def process(self, name: str, input_data: dict) -> str:
        """执行工具调用."""
        handler = self.get_handler(name)
        if handler is None:
            return f"Error: Unknown tool '{name}'"
        try:
            return handler(**input_data)
        except TypeError as exc:
            return f"Error: Invalid arguments for {name}: {exc}"
        except Exception as exc:
            return f"Error: {name} failed: {exc}"


# 全局注册表实例
_global_registry = ToolRegistry()


def register_tool(name: str, schema: dict) -> Callable:
    """
    装饰器: 注册工具到全局注册表.

    用法:
        @register_tool("my_tool", {
            "description": "My tool",
            "input_schema": {...}
        })
        def my_tool(arg: str) -> str:
            ...
    """
    def decorator(func: Callable) -> Callable:
        _global_registry.register(name, schema, func)
        return func
    return decorator


def get_registry() -> ToolRegistry:
    """获取全局工具注册表."""
    return _global_registry
