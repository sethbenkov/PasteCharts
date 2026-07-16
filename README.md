# tidbyt-agent-notify

Your Tidbyt stays the clock it already is — until an agent needs you.

When Claude Code finishes a task, Codex completes a turn, or any script
hits a milestone, a 64x32 notification card takes over the display:
a color-coded banner for the agent, a status icon (done / needs input /
error), and the message in a crisp pixel font. Long messages scroll as
a marquee. When the notification has played, the Tidbyt goes back to
its normal rotation — your clock.

Notifications that need action can be **pinned**: they join the app
rotation and keep coming back until you run `tidbyt-notify clear`.

No Pixlet or Starlark required — this renders WebP locally with Pillow
and pushes it through the official [Tidbyt HTTP API](https://tidbyt.dev).

## Setup

1. Install:

   ```sh
   pipx install .        # or: pip install .
   ```

2. Get your device ID and API token from the Tidbyt mobile app:
   your device → settings gear → **Get API key**.

3. Provide them via environment variables (or `--device`/`--token`
   flags, or `~/.config/tidbyt-notify/config.json` with keys
   `device_id` and `api_token`):

   ```sh
   export TIDBYT_DEVICE_ID="cheerful-example-device-123"
   export TIDBYT_API_TOKEN="eyJ..."
   ```

## Usage

```sh
# Shown once, then back to the clock
tidbyt-notify send "PR is ready for review" --agent claude --status done

# Needs action: stays in the rotation until cleared
tidbyt-notify send "Claude is waiting for input" --agent claude --status input --pin
tidbyt-notify clear

# Other agents / anything else
tidbyt-notify send "Codex turn complete" --agent codex --status done
tidbyt-notify send "Tests failed" --agent ci --status error

# Preview without a device (writes a WebP you can open)
tidbyt-notify send "Hello world" --agent claude --status done --dry-run --out preview.webp
```

Statuses: `done` (green, check), `input` (yellow, ?), `error` (red, !),
`working` (blue), `info` (white). Agents `claude`, `codex`, and
`shortcut` get preset banner colors; any other name gets a neutral
banner with the name uppercased.

## Hooking up your agents

### Claude Code

Copy `examples/claude-code-hook.sh` somewhere, `chmod +x` it, and merge
`examples/claude-code-settings.json` into `~/.claude/settings.json`.
You get:

- **Stop** events → "Claude is done" (green, shown once)
- **Notification** events (Claude waiting on you) → the actual message,
  yellow, pinned until you `tidbyt-notify clear`

### Codex CLI

Point Codex's notify hook at `examples/codex-notify.py` in
`~/.codex/config.toml`:

```toml
notify = ["python3", "/path/to/examples/codex-notify.py"]
```

### Everything else

`examples/generic.sh` shows the pattern — any tool that can run a shell
command (CI jobs, cron, Apple Shortcuts via SSH, a Makefile) can send
to the Tidbyt with one line.

## How the override works

The Tidbyt API's push endpoint interrupts the current rotation to show
a pushed image once — that's the default `send`. With `--pin` the image
is also installed into the rotation (installation ID `agentnotify`) so
it keeps cycling with your clock until `clear` deletes it. `--background`
with `--pin` adds it to the rotation without interrupting what's on
screen right now.

## Development

```sh
pip install -e .
tidbyt-notify send "test" --dry-run --out /tmp/test.webp
```
