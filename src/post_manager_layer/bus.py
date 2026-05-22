from __future__ import annotations

import threading
import traceback
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .events import ConsultContentEvent

Subscriber = Callable[["ConsultContentEvent"], None]


class EventBus:
    """Fan-out bus: each publish delivers the same event to all subscribers (async per handler)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._subscribers: list[Subscriber] = []

    def subscribe(self, handler: Subscriber) -> None:
        with self._lock:
            self._subscribers.append(handler)

    def publish(self, event: ConsultContentEvent) -> None:
        with self._lock:
            handlers = list(self._subscribers)
        for handler in handlers:

            def _run(h: Subscriber = handler, ev: ConsultContentEvent = event) -> None:
                try:
                    h(ev)
                except Exception:
                    traceback.print_exc()

            threading.Thread(target=_run, daemon=True).start()


_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    if _bus is None:
        raise RuntimeError("EventBus not initialized; call init_event_bus() first")
    return _bus


def init_event_bus() -> EventBus:
    global _bus
    _bus = EventBus()
    return _bus
