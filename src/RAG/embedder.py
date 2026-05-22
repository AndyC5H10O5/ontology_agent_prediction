from __future__ import annotations

from typing import Any

import httpx


def _extract_vector(data: dict[str, Any]) -> list[float]:
    if isinstance(data.get("embedding"), list):
        return [float(x) for x in data["embedding"]]
    embeddings = data.get("embeddings")
    if isinstance(embeddings, list) and embeddings:
        first = embeddings[0]
        if isinstance(first, list):
            return [float(x) for x in first]
    raise RuntimeError(f"Ollama embeddings 返回格式不支持: keys={list(data.keys())}")


def get_embedding(*, base_url: str, model: str, text: str, timeout: float = 120.0) -> list[float]:
    prompt = text.strip()
    if not prompt:
        raise ValueError("embedding 文本不能为空")
    root = base_url.rstrip("/")
    headers = {"Content-Type": "application/json"}

    # 兼容旧接口 /api/embeddings
    payload = {"model": model, "prompt": prompt}
    resp = httpx.post(f"{root}/api/embeddings", headers=headers, json=payload, timeout=timeout)
    if resp.status_code >= 400:
        # 尝试新接口 /api/embed
        fallback_payload = {"model": model, "input": [prompt]}
        resp = httpx.post(f"{root}/api/embed", headers=headers, json=fallback_payload, timeout=timeout)
    resp.raise_for_status()
    return _extract_vector(resp.json())
