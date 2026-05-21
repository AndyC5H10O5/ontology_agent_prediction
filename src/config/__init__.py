"""
src 配置包
"""

from .system_prompt import SYSTEM_PROMPT
from .llm_client import create_client, MODEL_ID

__all__ = ["SYSTEM_PROMPT", "create_client", "MODEL_ID"]
