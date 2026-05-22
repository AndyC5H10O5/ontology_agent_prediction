from __future__ import annotations

from pathlib import Path

from .paths import health_memory_path, skill_md_path, skills_by_id_dir


def read_health_memory(project_root: Path) -> str:
    path = health_memory_path(project_root)
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def write_health_memory(project_root: Path, content: str) -> None:
    path = health_memory_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_health_memory_block(project_root: Path) -> str:
    text = read_health_memory(project_root).strip()
    if not text:
        return ""
    return (
        "## 长期健康状况记忆（来自本地 harness/memory/personal_health.md，供你保持一致性；"
        "非诊断结论，以用户与执业医师为准）\n\n"
        f"{text}"
    )


def read_skill_md(project_root: Path, slug: str) -> str:
    path = skill_md_path(project_root, slug)
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def write_skill_md(project_root: Path, slug: str, content: str) -> None:
    base = skills_by_id_dir(project_root)
    base.mkdir(parents=True, exist_ok=True)
    skill_md_path(project_root, slug).write_text(content, encoding="utf-8")
