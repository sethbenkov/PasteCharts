#!/usr/bin/env bash
# Claude Code hook: forward hook events to the Tidbyt.
#
# Claude Code pipes a JSON payload on stdin. This script routes the two
# interesting events:
#   Stop         -> "Claude is done" (shown once, then back to your clock)
#   Notification -> the message, pinned until you run `tidbyt-notify clear`
#
# Wire it up in ~/.claude/settings.json (see claude-code-settings.json).
set -euo pipefail

payload=$(cat)

event=$(printf '%s' "$payload" | python3 -c \
  'import json,sys; print(json.load(sys.stdin).get("hook_event_name",""))')

case "$event" in
  Stop)
    tidbyt-notify send "Claude is done" --agent claude --status done
    ;;
  Notification)
    msg=$(printf '%s' "$payload" | python3 -c \
      'import json,sys; print(json.load(sys.stdin).get("message") or "Claude needs your input")')
    tidbyt-notify send "$msg" --agent claude --status input --pin
    ;;
esac
