from __future__ import annotations

from pathlib import Path
from typing import Any

from post_manager_layer.io import read_skill_md
from post_manager_layer.skills_consumer import load_skills_index, match_entries_for_query

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def tool_load_consult_skill(symptom_query: str) -> str:
    if not isinstance(symptom_query, str) or not symptom_query.strip():
        return "Error: symptom_query 必须为非空字符串"
    q = symptom_query.strip()
    data = load_skills_index(PROJECT_ROOT)
    entries = data.get("entries", [])
    if not isinstance(entries, list):
        entries = []
    matches = match_entries_for_query(entries, q)
    if not matches:
        return (
            "未在本地 skills 索引中找到与本次描述匹配的问诊 skill。"
            "请按常规步骤向用户收集信息；完成本轮后系统将生成并更新对应 skill。"
        )
    if len(matches) == 1:
        slug = matches[0].get("slug")
        if not slug:
            return "Error: 索引条目缺少 slug"
        body = read_skill_md(PROJECT_ROOT, str(slug)).strip()
        if not body:
            return (
                f"索引中存在条目（slug={slug}），但 skill 文件为空或缺失。"
                "请按常规范式收集；本轮结束并 submit_consult_content 后会写入 skill。"
            )
        return (
            f"已加载问诊 skill（slug: {slug}）。以下内容供你安排提问顺序，"
            "仍须遵守每次只向用户提一个清晰问题：\n\n"
            f"{body}"
        )
    lines: list[str] = [
        "找到多条可能相关的 skill，请先与用户确认主题或收窄描述后再加载；候选如下：",
    ]
    for m in matches:
        slug = m.get("slug", "")
        hint = m.get("symptom_course_hint", "")
        lines.append(f"- slug: {slug} | 主题线索: {hint}")
    return "\n".join(lines)


TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "load_consult_skill",
            "description": (
                "在新一轮问诊开始时调用：根据用户自述或症状主题线，从本地 skills/ 索引中查找"
                "已沉淀的「下次建议问题」skill。若命中一条则返回全文供你按序提问（每次仍只问一个问题）；"
                "未命中则按常规收集；多条命中时返回列表请用户择一或细化主题。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symptom_query": {
                        "type": "string",
                        "description": "用户原话摘要或症状主题线，用于与索引中的 symptom_course_hint / slug 做子串匹配。",
                    },
                },
                "required": ["symptom_query"],
            },
        },
    }
]

TOOL_HANDLERS: dict[str, Any] = {
    "load_consult_skill": tool_load_consult_skill,
}
