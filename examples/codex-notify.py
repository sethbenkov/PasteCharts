#!/usr/bin/env python3
"""Codex CLI notify hook: forward turn-complete events to the Tidbyt.

Codex invokes the configured notify program with a JSON payload as the
last argument. Enable it in ~/.codex/config.toml:

    notify = ["python3", "/path/to/examples/codex-notify.py"]
"""

import json
import subprocess
import sys


def main():
    try:
        event = json.loads(sys.argv[-1])
    except (IndexError, ValueError):
        return

    if event.get("type") != "agent-turn-complete":
        return

    message = event.get("last-assistant-message") or "Codex is done"
    # Keep it marquee-friendly; the Tidbyt scrolls long text but there
    # are limits to what you want crawling across 64 pixels.
    if len(message) > 120:
        message = message[:117] + "..."

    subprocess.run(
        ["tidbyt-notify", "send", message, "--agent", "codex", "--status", "done"],
        check=False,
    )


if __name__ == "__main__":
    main()
