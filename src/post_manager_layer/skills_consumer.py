from __future__ import annotations

import hashlib
import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.api_key import ModelConfig
from config.system_prompt import SKILLS_CONSUMER_SYSTEM_PROMPT

from .chat_client import post_chat_completion
from .events import ConsultContentEvent
from .io import read_skill_md, write_skill_md
from .paths import skills_index_path, skills_worker_log_path

_skills_write_lock = threading.Lock()


def skill_slug_from_course(symptom_course: str) -> str:
    raw = symptom_course.strip()
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    safe = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", raw, flags=re.UNICODE)[:40].strip("-") or "skill"
    combined = f"{safe}-{digest}"
    return combined[:120]


def load_skills_index(project_root: Path) -> dict[str, Any]:
    path = skills_index_path(project_root)
    if not path.exists():
        return {"entries": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("entries"), list):
            return data
    except (OSError, json.JSONDecodeError):
        pass
    return {"entries": []}


def save_skills_index(project_root: Path, data: dict[str, Any]) -> None:
    path = skills_index_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def match_entries_for_query(entries: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    q = query.strip().lower()
    if not q:
        return []
    matched: list[dict[str, Any]] = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        hint = str(e.get("symptom_course_hint") or "").strip().lower()
        slug = str(e.get("slug") or "").strip().lower()
        if q in hint or q in slug or (hint and hint in q):
            matched.append(e)
    return matched


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _log_skills_line(project_root: Path, line: str) -> None:
    path = skills_worker_log_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(line.rstrip() + "\n")
    except OSError:
        pass


def _validate_skills_output(text: str) -> bool:
    s = text.strip()
    if len(s) < 15:
        return False
    if "##" in s:
        return True
    if re.search(r"^\s*\d+\.\s+\S", s, re.MULTILINE):
        return True
    if re.search(r"^\s*[-*]\s+\S", s, re.MULTILINE):
        return True
    return False


def _build_skills_user_payload(existing_md: str, event: ConsultContentEvent) -> str:
    payload = json.dumps(event.to_payload_dict(), ensure_ascii=False, indent=2)
    return (
        f"【旧版 skill 全文】\n（若无则下面为空）\n\n{existing_md or '（空）'}\n\n"
        f"【本轮结构化问诊 JSON】\n{payload}\n"
    )


def _upsert_index_entry(
    project_root: Path, slug: str, symptom_course_hint: str, rel_path: str
) -> None:
    data = load_skills_index(project_root)
    entries = list(data.get("entries", []))
    now = _now_iso()
    found = False
    for i, e in enumerate(entries):
        if isinstance(e, dict) and e.get("slug") == slug:
            entries[i] = {
                "slug": slug,
                "symptom_course_hint": symptom_course_hint,
                "rel_path": rel_path,
                "updated_at": now,
            }
            found = True
            break
    if not found:
        entries.append(
            {
                "slug": slug,
                "symptom_course_hint": symptom_course_hint,
                "rel_path": rel_path,
                "updated_at": now,
            }
        )
    data["entries"] = entries
    save_skills_index(project_root, data)


def run_skills_consolidation(project_root: Path, config: ModelConfig, event: ConsultContentEvent) -> None:
    with _skills_write_lock:
        _run_skills_consolidation_locked(project_root, config, event)


def _run_skills_consolidation_locked(project_root: Path, config: ModelConfig, event: ConsultContentEvent) -> None:
    slug = skill_slug_from_course(event.symptom_course)
    rel_path = f"harness/skills/by_id/{slug}.md"
    existing = read_skill_md(project_root, slug)
    try:
        out = post_chat_completion(
            url=config.skills_chat_completions_url,
            api_key=config.skills_api_key,
            model=config.skills_model_id,
            messages=[
                {"role": "system", "content": SKILLS_CONSUMER_SYSTEM_PROMPT},
                {"role": "user", "content": _build_skills_user_payload(existing, event)},
            ],
        )
        if not out:
            _log_skills_line(project_root, "skills: empty model output")
            return
        if not _validate_skills_output(out):
            _log_skills_line(project_root, f"skills: rejected output (validation failed): {out[:200]!r}")
            return
        write_skill_md(project_root, slug, out)
        _upsert_index_entry(project_root, slug, event.symptom_course, rel_path)
    except Exception as exc:
        _log_skills_line(project_root, f"error: {exc!r}")


def make_skills_consumer(project_root: Path, config: ModelConfig):
    def _handler(event: ConsultContentEvent) -> None:
        run_skills_consolidation(project_root, config, event)

    return _handler
