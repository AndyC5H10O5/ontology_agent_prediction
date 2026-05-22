from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from config.system_prompt import HEALTH_AGENT_SYSTEM_PROMPT


@dataclass(frozen=True)
class ModelConfig:
    # 主 Agent 专用
    model_id: str
    api_key: str
    base_url: str
    chat_completions_url: str
    system_prompt: str
    # 记忆沉淀专用；默认与主 Agent 相同，可通过 MEMORY_* 环境变量单独切换
    memory_model_id: str
    memory_api_key: str
    memory_base_url: str
    memory_chat_completions_url: str
    memory_max_chars: int
    memory_min_chars: int
    # 问诊 skills 沉淀专用；默认与主 Agent 相同，可通过 SKILLS_* 环境变量单独切换
    skills_model_id: str
    skills_api_key: str
    skills_base_url: str
    skills_chat_completions_url: str
    # RAG 检索增强（Ollama Embedding + Chroma）
    rag_enabled: bool
    rag_kb_dir: str
    rag_chroma_dir: str
    rag_collection_name: str
    rag_ollama_base_url: str
    rag_embed_model: str
    rag_top_k: int
    rag_chunk_size: int
    rag_chunk_overlap: int


def load_model_config() -> ModelConfig:
    """Load model settings from environment variables."""
    env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(env_path, override=True)

    # 主 Agent 专用
    model_id = os.getenv("MODEL_ID", "deepseek-chat")
    api_key = os.getenv("DEEPSEEK_API_KEY", "")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    chat_completions_url = f"{base_url.rstrip('/')}/chat/completions"
    system_prompt = HEALTH_AGENT_SYSTEM_PROMPT

    # 记忆沉淀专用；默认与主 Agent 相同，可通过 MEMORY_* 环境变量单独切换
    memory_model_id = os.getenv("MEMORY_MODEL_ID") or model_id
    memory_api_key = os.getenv("MEMORY_API_KEY") or api_key
    memory_base_url = os.getenv("MEMORY_DEEPSEEK_BASE_URL") or base_url
    memory_chat_completions_url = f"{memory_base_url.rstrip('/')}/chat/completions"
    memory_max_chars = int(os.getenv("MEMORY_MAX_CHARS", "12000"))
    memory_min_chars = int(os.getenv("MEMORY_MIN_CHARS", "400"))

    # 问诊 skills 进化专用；默认与主 Agent 相同，可通过 SKILLS_* 环境变量单独切换
    skills_model_id = os.getenv("SKILLS_MODEL_ID") or model_id
    skills_api_key = os.getenv("SKILLS_API_KEY") or api_key
    skills_base_url = os.getenv("SKILLS_DEEPSEEK_BASE_URL") or base_url
    skills_chat_completions_url = f"{skills_base_url.rstrip('/')}/chat/completions"

    # RAG 配置（Ollama Embedding + Chroma）
    rag_enabled = os.getenv("RAG_ENABLED", "0").strip().lower() in {"1", "true", "yes", "on"}
    rag_kb_dir = os.getenv("RAG_KB_DIR", "harness/knowledge_base")
    rag_chroma_dir = os.getenv("RAG_CHROMA_DIR", "harness/chroma_db")
    rag_collection_name = os.getenv("RAG_COLLECTION_NAME", "health_knowledge")
    rag_ollama_base_url = os.getenv("RAG_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    rag_embed_model = os.getenv("RAG_EMBED_MODEL", "bge-m3")
    rag_top_k = int(os.getenv("RAG_TOP_K", "4"))
    rag_chunk_size = int(os.getenv("RAG_CHUNK_SIZE", "800"))
    rag_chunk_overlap = int(os.getenv("RAG_CHUNK_OVERLAP", "120"))

    return ModelConfig(
        model_id=model_id,
        api_key=api_key,
        base_url=base_url,
        chat_completions_url=chat_completions_url,
        system_prompt=system_prompt,
        memory_model_id=memory_model_id,
        memory_api_key=memory_api_key,
        memory_base_url=memory_base_url,
        memory_chat_completions_url=memory_chat_completions_url,
        memory_max_chars=memory_max_chars,
        memory_min_chars=memory_min_chars,
        skills_model_id=skills_model_id,
        skills_api_key=skills_api_key,
        skills_base_url=skills_base_url,
        skills_chat_completions_url=skills_chat_completions_url,
        rag_enabled=rag_enabled,
        rag_kb_dir=rag_kb_dir,
        rag_chroma_dir=rag_chroma_dir,
        rag_collection_name=rag_collection_name,
        rag_ollama_base_url=rag_ollama_base_url,
        rag_embed_model=rag_embed_model,
        rag_top_k=rag_top_k,
        rag_chunk_size=rag_chunk_size,
        rag_chunk_overlap=rag_chunk_overlap,
    )
