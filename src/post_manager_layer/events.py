from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class ConsultContentEvent:
    """Payload broadcast after submit_consult_content (one round of consult)."""

    symptom_course: str
    turns: tuple[dict[str, str], ...]
    session_id: str | None = None
    enqueued_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_payload_dict(self) -> dict[str, Any]:
        return {
            "symptom_course": self.symptom_course,
            "turns": [{"question": t.get("question", ""), "answer": t.get("answer", "")} for t in self.turns],
            "session_id": self.session_id,
            "enqueued_at": self.enqueued_at,
        }
