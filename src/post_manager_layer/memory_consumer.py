from __future__ import annotations

import json
import threading
from pathlib import Path

from config.api_key import ModelConfig
from config.system_prompt import (
    MEMORY_CONSUMER_COMPRESS_SYSTEM_PROMPT,
    MEMORY_CONSUMER_MERGE_SYSTEM_PROMPT,
)

_memory_write_lock = threading.Lock()

from .chat_client import post_chat_completion
from .events import ConsultContentEvent
from .io import read_health_memory, write_health_memory
from .paths import memory_worker_log_path


def _log_worker_line(project_root: Path, line: str) -> None:
    path = memory_worker_log_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("a", encoding="utf-8") as f:
            f.write(line.rstrip() + "\n")
    except OSError:
        pass


def _format_turns_for_prompt(turns: tuple[dict[str, str], ...]) -> str:
    lines: list[str] = []
    for i, t in enumerate(turns, start=1):
        q = (t.get("question") or "").strip()
        a = (t.get("answer") or "").strip()
        lines.append(f"{i}. 问：{q}\n   答：{a}")
    return "\n".join(lines)


def _merge_user_content(existing_md: str, event: ConsultContentEvent) -> str:
    consult_json = json.dumps(event.to_payload_dict(), ensure_ascii=False, indent=2)
    return (
        f"【已有记忆 Markdown】\n（若为空表示尚无记录）\n\n{existing_md or '（空）'}\n\n"
        f"【本轮问诊主题线 symptom_course】\n{event.symptom_course}\n\n"
        f"【本轮问答 turns】\n{_format_turns_for_prompt(event.turns)}\n\n"
        f"【结构化 JSON 副本（供对齐）】\n{consult_json}\n"
    )


def run_memory_consolidation(project_root: Path, config: ModelConfig, event: ConsultContentEvent) -> None:
    with _memory_write_lock:
        _run_memory_consolidation_locked(project_root, config, event)


def _run_memory_consolidation_locked(project_root: Path, config: ModelConfig, event: ConsultContentEvent) -> None:
    existing = read_health_memory(project_root)
    try:
        merged = post_chat_completion(
            url=config.memory_chat_completions_url,
            api_key=config.memory_api_key,
            model=config.memory_model_id,
            messages=[
                {"role": "system", "content": MEMORY_CONSUMER_MERGE_SYSTEM_PROMPT},
                {"role": "user", "content": _merge_user_content(existing, event)},
            ],
        )
        if not merged:
            _log_worker_line(project_root, "merge returned empty content")
            return

        out = merged
        if len(out) > config.memory_max_chars:
            target = max(config.memory_min_chars, int(0.1 * len(out)))
            compress_user = (
                f"目标：压缩后总长度大约不超过 {target} 个字符（当前约 {len(out)} 字符）。\n\n"
                f"【全文】\n{out}"
            )
            compressed = post_chat_completion(
                url=config.memory_chat_completions_url,
                api_key=config.memory_api_key,
                model=config.memory_model_id,
                messages=[
                    {"role": "system", "content": MEMORY_CONSUMER_COMPRESS_SYSTEM_PROMPT},
                    {"role": "user", "content": compress_user},
                ],
                max_tokens=8192,
            )
            if compressed:
                out = compressed

        write_health_memory(project_root, out)
    except Exception as exc:
        _log_worker_line(project_root, f"error: {exc!r}")


def make_memory_consumer(project_root: Path, config: ModelConfig):
    def _handler(event: ConsultContentEvent) -> None:
        run_memory_consolidation(project_root, config, event)

    return _handler
