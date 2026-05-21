"""
Agent 程序入口
"""

import os
import sys

from config import create_client, get_api_key, MODEL_ID, SYSTEM_PROMPT
from agent_core import AgentLoop
# 导入工具模块以触发注册
import tools  # noqa: F401

# ---------------------------------------------------------------------------
# API Provider
# ---------------------------------------------------------------------------

API_PROVIDER = os.getenv("API_PROVIDER", "anthropic")


def main() -> None:
    """程序入口."""
    api_key = get_api_key()
    if not api_key:
        print("\033[33mError: API Key 未设置.\033[0m")
        print("\033[2m请检查 .env 文件中的 API_KEY 配置.\033[0m")
        sys.exit(1)

    client = create_client()

    agent = AgentLoop(
        client=client,
        model_id=MODEL_ID,
        system_prompt=SYSTEM_PROMPT,
        provider=API_PROVIDER,
    )

    agent.run_repl()


if __name__ == "__main__":
    main()
