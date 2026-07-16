"""tidbyt-notify — agent notifications on a Tidbyt.

Renders a 64x32 notification card and pushes it to your Tidbyt, briefly
taking over from whatever is on screen (e.g. your clock). Pinned
notifications stay in the rotation until cleared.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from .push import TidbytError, delete_installation, push
from .render import AGENTS, STATUSES, render_frames, to_webp

PIN_INSTALLATION_ID = "agentnotify"
CONFIG_PATH = Path.home() / ".config" / "tidbyt-notify" / "config.json"


def _load_config():
    try:
        return json.loads(CONFIG_PATH.read_text())
    except (OSError, ValueError):
        return {}


def _credentials(args):
    cfg = _load_config()
    device = args.device or os.environ.get("TIDBYT_DEVICE_ID") or cfg.get("device_id")
    token = args.token or os.environ.get("TIDBYT_API_TOKEN") or cfg.get("api_token")
    missing = []
    if not device:
        missing.append("device ID (--device, $TIDBYT_DEVICE_ID, or config)")
    if not token:
        missing.append("API token (--token, $TIDBYT_API_TOKEN, or config)")
    if missing:
        sys.exit(
            "Missing " + " and ".join(missing) + ".\n"
            "Get both from the Tidbyt mobile app: your device -> settings gear "
            f"-> Get API key. Config file: {CONFIG_PATH}"
        )
    return device, token


def _add_credential_args(p):
    p.add_argument("--device", help="Tidbyt device ID (default: $TIDBYT_DEVICE_ID)")
    p.add_argument("--token", help="Tidbyt API token (default: $TIDBYT_API_TOKEN)")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="tidbyt-notify",
        description="Show agent notifications on a Tidbyt.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_send = sub.add_parser("send", help="render and push a notification")
    p_send.add_argument("message", help="notification text")
    p_send.add_argument(
        "--agent",
        default="agent",
        help="agent name; %s have preset colors, anything else gets a "
        "neutral banner" % "/".join(sorted(AGENTS)),
    )
    p_send.add_argument(
        "--status",
        default="info",
        choices=sorted(STATUSES),
        help="notification kind; sets text color and banner icon",
    )
    p_send.add_argument(
        "--pin",
        action="store_true",
        help="keep the notification in the app rotation until 'clear' is run",
    )
    p_send.add_argument(
        "--background",
        action="store_true",
        help="with --pin: add to rotation without interrupting the screen now",
    )
    p_send.add_argument(
        "--out",
        metavar="FILE.webp",
        help="also write the rendered WebP to a file",
    )
    p_send.add_argument(
        "--dry-run",
        action="store_true",
        help="render only; do not contact the Tidbyt API",
    )
    _add_credential_args(p_send)

    p_clear = sub.add_parser("clear", help="remove a pinned notification")
    _add_credential_args(p_clear)

    args = parser.parse_args(argv)

    if args.command == "clear":
        device, token = _credentials(args)
        try:
            delete_installation(device, token, PIN_INSTALLATION_ID)
        except TidbytError as e:
            sys.exit(str(e))
        print("Cleared pinned notification.")
        return

    frames = render_frames(args.message, agent=args.agent, status=args.status)
    webp = to_webp(frames)

    if args.out:
        Path(args.out).write_bytes(webp)
        print(f"Wrote {args.out} ({len(frames)} frame{'s' if len(frames) > 1 else ''})")

    if args.dry_run:
        if not args.out:
            print(f"Rendered {len(frames)} frame(s); --dry-run, nothing pushed.")
        return

    device, token = _credentials(args)
    try:
        push(
            device,
            token,
            webp,
            installation_id=PIN_INSTALLATION_ID if args.pin else None,
            background=args.background,
        )
    except TidbytError as e:
        sys.exit(str(e))
    where = "pinned to rotation" if args.pin else "shown once"
    print(f"Notification {where} on device {device}.")


if __name__ == "__main__":
    main()
