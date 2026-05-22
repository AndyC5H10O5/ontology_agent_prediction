from __future__ import annotations

import argparse
import json
from pathlib import Path

import chromadb


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect stored chunks in local Chroma DB.")
    parser.add_argument(
        "--db-path",
        default="harness/chroma_db",
        help="Path to Chroma persistent directory (default: harness/chroma_db).",
    )
    parser.add_argument(
        "--collection",
        default="health_knowledge",
        help="Collection name (default: health_knowledge).",
    )
    parser.add_argument(
        "--source",
        default="",
        help="Optional source_path filter for a specific file.",
    )
    parser.add_argument("--limit", type=int, default=10, help="Rows to fetch (default: 10).")
    parser.add_argument("--offset", type=int, default=0, help="Pagination offset (default: 0).")
    parser.add_argument(
        "--preview-chars",
        type=int,
        default=180,
        help="Preview length for each chunk text (default: 180).",
    )
    parser.add_argument(
        "--output-json",
        default="",
        help="Optional output JSON file path, e.g. treatment_plan/chunks_preview.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path = Path(args.db_path).resolve()
    client = chromadb.PersistentClient(path=str(db_path))
    collection = client.get_or_create_collection(args.collection)

    where = {"source_path": args.source} if args.source.strip() else None
    result = collection.get(
        where=where,
        limit=max(1, args.limit),
        offset=max(0, args.offset),
        include=["documents", "metadatas"],
    )

    ids = result.get("ids") or []
    docs = result.get("documents") or []
    metas = result.get("metadatas") or []

    rows: list[dict[str, str]] = []
    for i, chunk_id in enumerate(ids):
        doc = docs[i] if i < len(docs) else ""
        meta = metas[i] if i < len(metas) else {}
        text_preview = str(doc).replace("\n", " ").strip()[: max(20, args.preview_chars)]
        rows.append(
            {
                "id": str(chunk_id),
                "source_path": str(meta.get("source_path", "")),
                "chunk_id": str(meta.get("chunk_id", "")),
                "text_preview": text_preview,
            }
        )

    print(f"collection={args.collection}")
    print(f"db_path={db_path}")
    print(f"total_count={collection.count()}")
    print(f"returned={len(rows)} (offset={max(0, args.offset)}, limit={max(1, args.limit)})")
    print(json.dumps(rows, ensure_ascii=False, indent=2))

    if args.output_json.strip():
        out_path = Path(args.output_json).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"saved={out_path}")


if __name__ == "__main__":
    main()
