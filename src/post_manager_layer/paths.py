from __future__ import annotations

from pathlib import Path


def health_memory_relative() -> str:
    return "harness/memory/personal_health.md"


def consult_log_relative() -> str:
    return "logs/consult_content.jsonl"


def memory_worker_log_relative() -> str:
    return "logs/memory_worker.log"


def health_memory_path(project_root: Path) -> Path:
    return project_root / health_memory_relative()


def consult_log_path(project_root: Path) -> Path:
    return project_root / consult_log_relative()


def memory_worker_log_path(project_root: Path) -> Path:
    return project_root / memory_worker_log_relative()


def skills_index_relative() -> str:
    return "harness/skills/index.json"


def skills_by_id_relative() -> str:
    return "harness/skills/by_id"


def skills_worker_log_relative() -> str:
    return "logs/skills_worker.log"


def skills_index_path(project_root: Path) -> Path:
    return project_root / skills_index_relative()


def skills_by_id_dir(project_root: Path) -> Path:
    return project_root / skills_by_id_relative()


def skill_md_path(project_root: Path, slug: str) -> Path:
    safe = slug.replace("/", "").replace("\\", "")
    return skills_by_id_dir(project_root) / f"{safe}.md"


def skills_worker_log_path(project_root: Path) -> Path:
    return project_root / skills_worker_log_relative()
