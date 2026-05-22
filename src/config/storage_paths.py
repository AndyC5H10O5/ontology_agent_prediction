from __future__ import annotations

from pathlib import Path


def harness_dir(project_root: Path) -> Path:
    return project_root / "harness"


def harness_memory_dir(project_root: Path) -> Path:
    return harness_dir(project_root) / "memory"


def harness_session_dir(project_root: Path) -> Path:
    return harness_dir(project_root) / "session"


def harness_skills_dir(project_root: Path) -> Path:
    return harness_dir(project_root) / "skills"


def harness_knowledge_base_dir(project_root: Path) -> Path:
    return harness_dir(project_root) / "knowledge_base"


def harness_chroma_dir(project_root: Path) -> Path:
    return harness_dir(project_root) / "chroma_db"
