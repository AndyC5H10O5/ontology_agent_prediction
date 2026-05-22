from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


@dataclass
class SessionMeta:
    session_id: str
    label: str
    created_at: str
    last_active: str
    message_count: int


class SessionStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base_dir / "index.json"
        self._index: dict[str, dict[str, Any]] = self._load_index()
        self.current_session_id: str | None = None

    def _load_index(self) -> dict[str, dict[str, Any]]:
        if not self.index_path.exists():
            return {}
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            pass
        return {}

    def _save_index(self) -> None:
        self.index_path.write_text(
            json.dumps(self._index, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _session_path(self, session_id: str) -> Path:
        return self.base_dir / f"{session_id}.json"

    def create_session(self, label: str | None = None) -> str:
        now = _now_iso()
        session_id = uuid4().hex[:12]
        session_label = label.strip() if label and label.strip() else f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self._index[session_id] = {
            "id": session_id,
            "label": session_label,
            "created_at": now,
            "last_active": now,
            "message_count": 0,
        }
        self._session_path(session_id).write_text("[]", encoding="utf-8")
        self.current_session_id = session_id
        self._save_index()
        return session_id

    def list_sessions(self) -> list[SessionMeta]:
        sessions: list[SessionMeta] = []
        for sid, meta in self._index.items():
            sessions.append(
                SessionMeta(
                    session_id=sid,
                    label=str(meta.get("label") or sid),
                    created_at=str(meta.get("created_at") or ""),
                    last_active=str(meta.get("last_active") or ""),
                    message_count=int(meta.get("message_count") or 0),
                )
            )
        sessions.sort(key=lambda item: item.last_active, reverse=True)
        return sessions

    def resolve_session(self, selector: str, sessions: list[SessionMeta]) -> str:
        token = selector.strip()
        if token.isdigit():
            idx = int(token)
            if idx < 1 or idx > len(sessions):
                raise ValueError(f"会话编号超出范围: 1-{len(sessions)}")
            return sessions[idx - 1].session_id

        matches = [item.session_id for item in sessions if item.session_id.startswith(token)]
        if not matches:
            raise ValueError(f"未找到会话: {selector}")
        if len(matches) > 1:
            raise ValueError(f"会话前缀不唯一: {selector}")
        return matches[0]

    def find_prefix_matches(self, prefix: str) -> list[SessionMeta]:
        sessions = self.list_sessions()
        return [item for item in sessions if item.session_id.startswith(prefix)]

    def get_label(self, session_id: str) -> str:
        meta = self._index.get(session_id) or {}
        label = str(meta.get("label") or "").strip()
        return label or session_id

    def switch_session(self, selector: str) -> tuple[str, list[dict[str, Any]]]:
        sessions = self.list_sessions()
        if not sessions:
            raise ValueError("暂无可切换会话")
        target = self.resolve_session(selector, sessions)
        messages = self.load_messages(target)
        self.current_session_id = target
        self._touch(target, len(messages))
        return target, messages

    def delete_session(self, selector: str) -> tuple[str, str | None, list[dict[str, Any]] | None]:
        sessions = self.list_sessions()
        if not sessions:
            raise ValueError("暂无可删除会话")
        target = self.resolve_session(selector, sessions)

        path = self._session_path(target)
        if path.exists():
            path.unlink()
        self._index.pop(target, None)

        if not self._index:
            self._save_index()
            sid = self.create_session("initial")
            return target, sid, []

        if self.current_session_id == target:
            self._save_index()
            sid, messages = self.load_recent_or_create()
            return target, sid, messages

        self._save_index()
        return target, None, None

    def load_recent_or_create(self) -> tuple[str, list[dict[str, Any]]]:
        sessions = self.list_sessions()
        if sessions:
            sid = sessions[0].session_id
            self.current_session_id = sid
            messages = self.load_messages(sid)
            self._touch(sid, len(messages))
            return sid, messages
        sid = self.create_session("initial")
        return sid, []

    def load_messages(self, session_id: str) -> list[dict[str, Any]]:
        path = self._session_path(session_id)
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
        except Exception:
            pass
        return []

    def save_messages(self, session_id: str, messages: list[dict[str, Any]]) -> None:
        self._session_path(session_id).write_text(
            json.dumps(messages, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._touch(session_id, len(messages))

    def _touch(self, session_id: str, message_count: int) -> None:
        if session_id not in self._index:
            self._index[session_id] = {"id": session_id, "label": session_id, "created_at": _now_iso()}
        self._index[session_id]["last_active"] = _now_iso()
        self._index[session_id]["message_count"] = message_count
        self._save_index()

