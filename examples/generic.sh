#!/usr/bin/env bash
# Any tool that can run a shell command can notify your Tidbyt.
# Examples:

# Task finished fine
tidbyt-notify send "Build passed" --agent ci --status done

# Something needs you; stays on the Tidbyt rotation until cleared
tidbyt-notify send "Deploy waiting for approval" --agent ci --status input --pin

# Something broke
tidbyt-notify send "Tests failed on main" --agent ci --status error

# Back to just the clock
tidbyt-notify clear

# Long-running command wrapper: notify on exit either way
run-and-notify() {
  if "$@"; then
    tidbyt-notify send "Done: $*" --status done
  else
    tidbyt-notify send "FAILED: $*" --status error --pin
  fi
}
