from __future__ import annotations

import sys

from agent_core.loop_core import agent_loop
from cli.display import print_error
from config.api_key import load_model_config

def main() -> None:
    config = load_model_config()
    if not config.api_key:
        print_error("Error: API_KEY 未设置.")
        sys.exit(1)

    agent_loop(config)


if __name__ == "__main__":
    main()
