from __future__ import annotations

from contextvars import ContextVar

_consult_session_id: ContextVar[str | None] = ContextVar("consult_session_id", default=None)


def set_consult_session_id(session_id: str | None) -> None:
    _consult_session_id.set(session_id)


def get_consult_session_id() -> str | None:
    return _consult_session_id.get()
