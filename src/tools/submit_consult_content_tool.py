from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from post_manager_layer import ConsultContentEvent, get_event_bus
from post_manager_layer.context import get_consult_session_id
from post_manager_layer.paths import consult_log_path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _validate_turns(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list) or not raw:
        raise ValueError("turns 必须为非空数组")
    out: list[dict[str, str]] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"turns[{i}] 必须为对象")
        q = item.get("question", "")
        a = item.get("answer", "")
        if not isinstance(q, str) or not isinstance(a, str):
            raise ValueError(f"turns[{i}] 的 question/answer 必须为字符串")
        q, a = q.strip(), a.strip()
        if not q or not a:
            raise ValueError(f"turns[{i}] 的 question 与 answer 去空格后均不可为空")
        out.append({"question": q, "answer": a})
    return out


def tool_submit_consult_content(symptom_course: str, turns: list[Any]) -> str:
    if not isinstance(symptom_course, str) or not symptom_course.strip():
        return "Error: symptom_course 必须为非空字符串"
    try:
        clean_turns = _validate_turns(turns)
    except ValueError as exc:
        return f"Error: {exc}"

    sc = symptom_course.strip()
    event = ConsultContentEvent(
        symptom_course=sc,
        turns=tuple(clean_turns),
        session_id=get_consult_session_id(),
    )

    log_path = consult_log_path(PROJECT_ROOT)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "session_id": event.session_id,
        "symptom_course": sc,
        "turns": clean_turns,
    }
    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    try:
        get_event_bus().publish(event)
    except RuntimeError:
        return "Error: 事件总线未初始化（内部错误）"

    return (
        "已记录本轮问诊结构化内容并排入记忆更新队列；"
        f"共 {len(clean_turns)} 轮问答。请继续输出方案并调用 write_file。"
    )


TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "submit_consult_content",
            "description": (
                "在信息收集已足够、即将生成并保存个人治疗方案之前，必须调用一次："
                "提交本轮多轮问诊的去噪结构化快照。顶层仅含 symptom_course（本轮主题线一句）"
                "与 turns（每轮助理 question + 用户 answer，按时间顺序）。"
                "禁止在顶层堆砌主诉/分系统症状等医学分类字段；细节放在问答文本中。"
                "调用成功后，再在后续步骤使用 write_file 写入 treatment_plan/ 下的方案。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symptom_course": {
                        "type": "string",
                        "description": "本轮问诊简短主题线（如主要困扰与时间线一句），非诊断标签。",
                    },
                    "turns": {
                        "type": "array",
                        "description": "按时间顺序的问答轮次；每项含助理提问与用户回答（均已去噪）。",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question": {"type": "string"},
                                "answer": {"type": "string"},
                            },
                            "required": ["question", "answer"],
                        },
                    },
                },
                "required": ["symptom_course", "turns"],
            },
        },
    }
]

TOOL_HANDLERS: dict[str, Any] = {
    "submit_consult_content": tool_submit_consult_content,
}
