from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb

from .embedder import get_embedding


def _get_collection(*, chroma_dir: Path, collection_name: str):
    client = chromadb.PersistentClient(path=str(chroma_dir))
    return client.get_or_create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})


def upsert_chunks(
    *,
    chroma_dir: Path,
    collection_name: str,
    base_url: str,
    embed_model: str,
    items: list[dict[str, str]],
) -> int:
    collection = _get_collection(chroma_dir=chroma_dir, collection_name=collection_name)
    if not items:
        return 0
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, str]] = []
    embeddings: list[list[float]] = []

    for item in items:
        text = (item.get("text") or "").strip()
        if not text:
            continue
        ids.append(item["chunk_id"])
        documents.append(text)
        metadatas.append({"source_path": item["source_path"], "chunk_id": item["chunk_id"]})
        embeddings.append(get_embedding(base_url=base_url, model=embed_model, text=text))

    if not ids:
        return 0
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    return len(ids)


def query_knowledge(
    *,
    chroma_dir: Path,
    collection_name: str,
    base_url: str,
    embed_model: str,
    query: str,
    top_k: int,
) -> list[dict[str, Any]]:
    q = query.strip()
    if not q:
        return []
    collection = _get_collection(chroma_dir=chroma_dir, collection_name=collection_name)
    q_emb = get_embedding(base_url=base_url, model=embed_model, text=q)
    data = collection.query(query_embeddings=[q_emb], n_results=max(1, top_k), include=["documents", "metadatas", "distances"])

    documents = (data.get("documents") or [[]])[0]
    metadatas = (data.get("metadatas") or [[]])[0]
    distances = (data.get("distances") or [[]])[0]
    out: list[dict[str, Any]] = []
    for i, doc in enumerate(documents):
        meta = metadatas[i] if i < len(metadatas) else {}
        dist = distances[i] if i < len(distances) else None
        out.append(
            {
                "snippet": str(doc or "").strip(),
                "source_path": str((meta or {}).get("source_path") or ""),
                "chunk_id": str((meta or {}).get("chunk_id") or ""),
                "score": None if dist is None else float(1.0 - float(dist)),
            }
        )
    return out
