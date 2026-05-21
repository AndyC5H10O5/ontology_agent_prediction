"""
Agent 循环核心实现

支持 Anthropic 和 DeepSeek (OpenAI 兼容) API。
"""

from typing import Any

from config import MODEL_ID
from tools import get_registry

# ---------------------------------------------------------------------------
# ANSI 颜色
# ---------------------------------------------------------------------------

CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"
BOLD = "\033[1m"


def colored_prompt() -> str:
    return f"{CYAN}{BOLD}You > {RESET}"


def print_assistant(text: str) -> None:
    print(f"\n{GREEN}{BOLD}Assistant:{RESET} {text}\n")


def print_tool(name: str, detail: str) -> None:
    print(f"  {DIM}[tool: {name}] {detail}{RESET}")


def print_info(text: str) -> None:
    print(f"{DIM}{text}{RESET}")


# ---------------------------------------------------------------------------
# Agent Loop 类
# ---------------------------------------------------------------------------


class AgentLoop:
    """智能体主循环类."""

    def __init__(
        self,
        client,
        model_id: str,
        system_prompt: str = "You are a helpful AI assistant.",
        max_tokens: int = 8096,
        provider: str = "anthropic",
    ):
        self.client = client
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.provider = provider
        self.messages: list[dict] = []
        self._registry = get_registry()

    def _call_api_anthropic(self) -> Any:
        """调用 Anthropic API."""
        tools = self._registry.get_tools()
        return self.client.messages.create(
            model=self.model_id,
            max_tokens=self.max_tokens,
            system=self.system_prompt,
            tools=tools if tools else None,
            messages=self.messages,
        )

    def _call_api_openai(self) -> Any:
        """调用 OpenAI 兼容 API (DeepSeek)."""
        tools = self._registry.get_tools()

        # 转换消息格式
        openai_messages = [{"role": "system", "content": self.system_prompt}]
        openai_messages.extend(self.messages)

        # 转换工具格式
        openai_tools = None
        if tools:
            openai_tools = []
            for tool in tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("input_schema", {}),
                    }
                })

        return self.client.chat.completions.create(
            model=self.model_id,
            max_tokens=self.max_tokens,
            messages=openai_messages,
            tools=openai_tools,
        )

    def _call_api(self) -> Any:
        """调用 LLM API."""
        if self.provider == "anthropic":
            return self._call_api_anthropic()
        else:
            return self._call_api_openai()

    def _process_tool_use_anthropic(self, response: Any) -> None:
        """处理 Anthropic tool_use."""
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            print_tool(block.name, str(block.input)[:50])
            result = self._registry.process(block.name, block.input)

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })

        self.messages.append({
            "role": "user",
            "content": tool_results,
        })

    def _process_tool_use_openai(self, response: Any) -> None:
        """处理 OpenAI 兼容 tool_use."""
        message = response.choices[0].message

        # 追加 assistant 消息
        self.messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": message.tool_calls,
        })

        if not message.tool_calls:
            return

        # 处理工具调用
        for tool_call in message.tool_calls:
            import json
            tool_name = tool_call.function.name
            tool_input = json.loads(tool_call.function.arguments)

            print_tool(tool_name, str(tool_input)[:50])
            result = self._registry.process(tool_name, tool_input)

            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

    def _process_end_turn_anthropic(self, response: Any) -> str:
        """处理 Anthropic end_turn."""
        assistant_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                assistant_text += block.text
        return assistant_text

    def _process_end_turn_openai(self, response: Any) -> str:
        """处理 OpenAI 兼容 end_turn."""
        return response.choices[0].message.content or ""

    def _is_tool_use_anthropic(self, response: Any) -> bool:
        """检查 Anthropic 是否需要工具调用."""
        return response.stop_reason == "tool_use"

    def _is_tool_use_openai(self, response: Any) -> bool:
        """检查 OpenAI 是否需要工具调用."""
        return response.choices[0].finish_reason == "tool_calls"

    def run_turn(self, user_input: str) -> str:
        """执行一轮对话."""
        self.messages.append({
            "role": "user",
            "content": user_input,
        })

        while True:
            try:
                response = self._call_api()
            except Exception as exc:
                print_info(f"API Error: {exc}")
                while self.messages and self.messages[-1]["role"] != "user":
                    self.messages.pop()
                if self.messages:
                    self.messages.pop()
                return ""

            if self.provider == "anthropic":
                # Anthropic 流程
                self.messages.append({
                    "role": "assistant",
                    "content": response.content,
                })

                if self._is_tool_use_anthropic(response):
                    self._process_tool_use_anthropic(response)
                    continue
                else:
                    return self._process_end_turn_anthropic(response)

            else:
                # OpenAI 兼容流程
                if self._is_tool_use_openai(response):
                    self._process_tool_use_openai(response)
                    continue
                else:
                    return self._process_end_turn_openai(response)

    def run_repl(self) -> None:
        """运行交互式 REPL."""
        tools = self._registry.get_tools()
        print_info("=" * 60)
        print_info("  Agent Core  |  Interactive REPL")
        print_info(f"  Provider: {self.provider}")
        print_info(f"  Model: {self.model_id}")
        print_info(f"  Tools: {', '.join(t['name'] for t in tools) if tools else 'none'}")
        print_info("  输入 'quit' 或 'exit' 退出, Ctrl+C 同样有效.")
        print_info("=" * 60)
        print()

        while True:
            try:
                user_input = input(colored_prompt()).strip()
            except (KeyboardInterrupt, EOFError):
                print(f"\n{DIM}再见.{RESET}")
                break

            if not user_input:
                continue

            if user_input.lower() in ("quit", "exit"):
                print(f"{DIM}再见.{RESET}")
                break

            response_text = self.run_turn(user_input)
            if response_text:
                print_assistant(response_text)
