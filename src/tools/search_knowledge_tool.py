from __future__ import annotations

from pathlib import Path
from typing import Any

from config.api_key import load_model_config
from RAG.retriever import query_knowledge

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def tool_search_knowledge(query: str, top_k: int | None = None) -> str:
    if not isinstance(query, str) or not query.strip():
        return "Error: query 必须为非空字符串"
    config = load_model_config()
    if not config.rag_enabled:
        return "Error: RAG 未启用（请设置 RAG_ENABLED=1 并完成索引构建）"

    try:
        results = query_knowledge(
            chroma_dir=(PROJECT_ROOT / config.rag_chroma_dir).resolve(),
            collection_name=config.rag_collection_name,
            base_url=config.rag_ollama_base_url,
            embed_model=config.rag_embed_model,
            query=query,
            top_k=top_k or config.rag_top_k,
        )
    except Exception as exc:
        return f"Error: knowledge search failed: {exc}"

    if not results:
        return "未检索到相关知识片段。"

    lines = [f"检索到 {len(results)} 条知识片段："]
    for i, item in enumerate(results, start=1):
        score = item.get("score")
        score_text = "N/A" if score is None else f"{float(score):.4f}"
        snippet = str(item.get("snippet") or "").replace("\n", " ").strip()
        lines.append(
            f"{i}. score={score_text} | source={item.get('source_path')} | chunk_id={item.get('chunk_id')}\n"
            f"   snippet: {snippet}"
        )
    return "\n".join(lines)


TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": (
                "从本地 RAG 知识库召回与当前症状/方案生成相关的证据片段。"
                "建议在成稿前调用，用于增强专业分析。返回片段内容、来源路径、chunk_id、相关性分数。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索查询语句，建议包含症状主题和关键问题。"},
                    "top_k": {"type": "integer", "description": "可选，返回条数上限。"},
                },
                "required": ["query"],
            },
        },
    }
]

TOOL_HANDLERS: dict[str, Any] = {
    "search_knowledge": tool_search_knowledge,
}
