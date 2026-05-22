from __future__ import annotations

import httpx
import json
from pathlib import Path
from typing import Any

from cli.display import colored_prompt, print_assistant, print_error, print_info
from config.api_key import ModelConfig
from config.storage_paths import harness_session_dir
from post_manager_layer import read_health_memory_block, setup_post_manager_layer
from post_manager_layer.context import set_consult_session_id
from session_store import SessionStore, format_short_id, handle_session_command
from tools import TOOLS, process_tool_call


def agent_loop(config: ModelConfig) -> None:
    """Main agent REPL loop."""
    project_root = Path(__file__).resolve().parents[2]

    # 初始化记忆沉淀管理（异步队列）
    setup_post_manager_layer(project_root, config)
    
    store = SessionStore(harness_session_dir(project_root))
    current_session_id, messages = store.load_recent_or_create()

    print_info("=" * 80)
    print_info("  Personal Health Agent Assistant")
    print_info(f"  Model: {config.model_id}")
    print_info(f"  Session: {store.get_label(current_session_id)}")
    print_info("  会话管理指令: /list, /new [会话名], /switch [idx], /delete [idx]")
    print_info("  输入 'quit' / 'exit' 退出. Ctrl+C 同样有效.")
    print_info("=" * 80)
    print()

    while True:
        try:
            user_input = input(colored_prompt()).strip()
        except (KeyboardInterrupt, EOFError):
            print_info("再见.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("quit", "exit"):
            print_info("再见.")
            break

        handled, switched_messages = handle_session_command(user_input, store)
        if handled:
            if switched_messages is not None:
                messages = switched_messages
                current_session_id = store.current_session_id or current_session_id
            continue

        messages.append({"role": "user", "content": user_input})

        while True:
            try:
                memory_block = read_health_memory_block(project_root)
                system_content = (
                    f"{config.system_prompt}\n\n{memory_block}" if memory_block else config.system_prompt
                )
                payload_messages = [{"role": "system", "content": system_content}] + messages
                response = httpx.post(
                    config.chat_completions_url,
                    headers={
                        "Authorization": f"Bearer {config.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": config.model_id,
                        "messages": payload_messages,
                        "max_tokens": 4096,
                        "tools": TOOLS,
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()
            except Exception as exc:
                print_error(f"\nAPI Error: {exc}\n")
                while messages and messages[-1].get("role") != "user":
                    messages.pop()
                if messages and messages[-1].get("role") == "user":
                    messages.pop()
                store.save_messages(current_session_id, messages)
                break

            choice = (data.get("choices") or [{}])[0]
            message = choice.get("message") or {}
            finish_reason = choice.get("finish_reason")
            assistant_text = (message.get("content") or "").strip()
            tool_calls = message.get("tool_calls") or []

            if tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_text or "",
                        "tool_calls": tool_calls,
                    }
                )

                for tool_call in tool_calls:
                    tool_call_id = tool_call.get("id", "")
                    function_obj = tool_call.get("function") or {}
                    tool_name = function_obj.get("name", "")
                    raw_arguments = function_obj.get("arguments") or "{}"

                    try:
                        tool_input = json.loads(raw_arguments)
                        if not isinstance(tool_input, dict):
                            tool_input = {}
                    except json.JSONDecodeError as exc:
                        tool_result = f"Error: Invalid tool arguments JSON: {exc}"
                    else:
                        set_consult_session_id(current_session_id)
                        try:
                            tool_result = process_tool_call(tool_name, tool_input)
                        finally:
                            set_consult_session_id(None)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": tool_name,
                            "content": tool_result,
                        }
                    )

                continue

            if assistant_text:
                print_assistant(assistant_text)
            else:
                print_info("[warning] 模型返回了空内容.")

            if finish_reason:
                print_info(f"[finish_reason={finish_reason}]")

            messages.append({"role": "assistant", "content": assistant_text})
            store.save_messages(current_session_id, messages)
            break
