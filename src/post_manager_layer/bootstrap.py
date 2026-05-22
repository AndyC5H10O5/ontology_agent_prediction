from __future__ import annotations

from pathlib import Path

from config.api_key import ModelConfig

from .bus import EventBus, init_event_bus
from .memory_consumer import make_memory_consumer
from .skills_consumer import make_skills_consumer


def setup_post_manager_layer(project_root: Path, config: ModelConfig) -> EventBus:
    bus = init_event_bus()
    bus.subscribe(make_memory_consumer(project_root, config))
    bus.subscribe(make_skills_consumer(project_root, config))
    return bus
