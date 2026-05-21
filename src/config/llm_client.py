"""
LLM 客户端配置

支持:
    - Anthropic Claude API
    - DeepSeek API (OpenAI 兼容)
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env", override=True)

# ---------------------------------------------------------------------------
# 配置项
# ---------------------------------------------------------------------------

# API 提供商: "anthropic" 或 "deepseek"
API_PROVIDER = os.getenv("API_PROVIDER", "anthropic")

# Anthropic 配置
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_BASE_URL = os.getenv("ANTHROPIC_BASE_URL") or None
ANTHROPIC_MODEL = os.getenv("MODEL_ID", "claude-sonnet-4-20250514")

# DeepSeek 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ---------------------------------------------------------------------------
# 模型 ID (根据 provider 选择)
# ---------------------------------------------------------------------------

MODEL_ID = ANTHROPIC_MODEL if API_PROVIDER == "anthropic" else DEEPSEEK_MODEL

# ---------------------------------------------------------------------------
# 客户端创建
# ---------------------------------------------------------------------------


def create_client():
    """
    创建 LLM 客户端.

    Returns:
        Anthropic 客户端 (provider=anthropic)
        OpenAI 客户端 (provider=deepseek)
    """
    if API_PROVIDER == "anthropic":
        from anthropic import Anthropic
        return Anthropic(
            api_key=ANTHROPIC_API_KEY,
            base_url=ANTHROPIC_BASE_URL,
        )

    elif API_PROVIDER == "deepseek":
        from openai import OpenAI
        return OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )

    else:
        raise ValueError(f"Unknown API_PROVIDER: {API_PROVIDER}")


def get_api_key() -> str:
    """获取当前 provider 的 API key."""
    if API_PROVIDER == "anthropic":
        return ANTHROPIC_API_KEY
    elif API_PROVIDER == "deepseek":
        return DEEPSEEK_API_KEY
    else:
        raise ValueError(f"Unknown API_PROVIDER: {API_PROVIDER}")
