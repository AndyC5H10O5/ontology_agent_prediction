from __future__ import annotations

from pathlib import Path

from .chunking import chunk_text
from .doc_loader import iter_kb_files, load_document_text
from .retriever import upsert_chunks


def build_index(
    *,
    project_root: Path,
    kb_dir: str,
    chroma_dir: str,
    collection_name: str,
    ollama_base_url: str,
    embed_model: str,
    chunk_size: int,
    chunk_overlap: int,
) -> dict[str, int]:
    kb_root = (project_root / kb_dir).resolve()
    db_root = (project_root / chroma_dir).resolve()
    db_root.mkdir(parents=True, exist_ok=True)

    if not kb_root.exists():
        raise FileNotFoundError(f"知识库目录不存在: {kb_root}")

    files = iter_kb_files(kb_root)
    total_chunks = 0
    total_files = 0
    for file_path in files:
        text = load_document_text(file_path)
        rel = file_path.relative_to(project_root).as_posix()
        chunks = chunk_text(
            text=text,
            source_path=rel,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        items = [{"chunk_id": c.chunk_id, "source_path": c.source_path, "text": c.text} for c in chunks]
        total_chunks += upsert_chunks(
            chroma_dir=db_root,
            collection_name=collection_name,
            base_url=ollama_base_url,
            embed_model=embed_model,
            items=items,
        )
        total_files += 1
    return {"files": total_files, "chunks": total_chunks}
