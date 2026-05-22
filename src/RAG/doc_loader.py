from __future__ import annotations

import html
import re
import zipfile
from pathlib import Path


def _read_pdf(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except Exception as exc:  # pragma: no cover - dependency/runtime guard
        raise RuntimeError("读取 PDF 需要安装 pypdf") from exc

    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        parts.append((page.extract_text() or "").strip())
    return "\n\n".join(p for p in parts if p)


def _strip_html_tags(text: str) -> str:
    no_scripts = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    no_tags = re.sub(r"(?s)<[^>]+>", " ", no_scripts)
    unescaped = html.unescape(no_tags)
    cleaned = re.sub(r"\s+", " ", unescaped).strip()
    return cleaned


def _read_epub(path: Path) -> str:
    parts: list[str] = []
    with zipfile.ZipFile(path, "r") as zf:
        for name in zf.namelist():
            lower = name.lower()
            if not lower.endswith((".xhtml", ".html", ".htm")):
                continue
            raw = zf.read(name)
            text = raw.decode("utf-8", errors="ignore")
            body = _strip_html_tags(text)
            if body:
                parts.append(body)
    return "\n\n".join(parts)


def load_document_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        return _read_pdf(path)
    if suffix == ".epub":
        return _read_epub(path)
    raise ValueError(f"Unsupported file type: {path.name}")


def iter_kb_files(kb_dir: Path) -> list[Path]:
    files: list[Path] = []
    for p in kb_dir.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() not in {".md", ".txt", ".pdf", ".epub"}:
            continue
        files.append(p)
    files.sort()
    return files
