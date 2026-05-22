from __future__ import annotations

from pathlib import Path

from config.api_key import load_model_config
from RAG.index_builder import build_index


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    config = load_model_config()
    stats = build_index(
        project_root=project_root,
        kb_dir=config.rag_kb_dir,
        chroma_dir=config.rag_chroma_dir,
        collection_name=config.rag_collection_name,
        ollama_base_url=config.rag_ollama_base_url,
        embed_model=config.rag_embed_model,
        chunk_size=config.rag_chunk_size,
        chunk_overlap=config.rag_chunk_overlap,
    )
    print(
        f"RAG 索引构建完成: files={stats['files']} chunks={stats['chunks']} "
        f"collection={config.rag_collection_name}"
    )


if __name__ == "__main__":
    main()
