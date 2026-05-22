from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    text: str
    source_path: str


def chunk_text(
    *,
    text: str,
    source_path: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[TextChunk]:
    body = text.strip()
    if not body:
        return []
    size = max(100, chunk_size)
    overlap = max(0, min(chunk_overlap, size - 1))
    step = max(1, size - overlap)

    chunks: list[TextChunk] = []
    start = 0
    idx = 0
    while start < len(body):
        end = min(len(body), start + size)
        chunk = body[start:end].strip()
        if chunk:
            chunks.append(
                TextChunk(
                    chunk_id=f"{source_path}#{idx}",
                    text=chunk,
                    source_path=source_path,
                )
            )
            idx += 1
        if end >= len(body):
            break
        start += step
    return chunks
