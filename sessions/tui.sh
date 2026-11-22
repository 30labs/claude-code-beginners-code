#!/usr/bin/env bash
# Drive an interactive session started by record.sh --tui.
#
#   sessions/tui.sh <id> type "<text>"   type text, then Enter
#   sessions/tui.sh <id> ask "<text>"    type, wait for the turn to end
#   sessions/tui.sh <id> key <key>...    tmux key names: Escape, S-Tab
#   sessions/tui.sh <id> snap <name>     save the screen to <id>/screens/
#   sessions/tui.sh <id> show            print the screen
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
id=$1
cmd=$2
shift 2
pane="tally-$id"

turns() {
  tmux capture-pane -p -S - -t "$pane" | grep -c '✻ .* done' || true
}

case $cmd in
  ask)
    before=$(turns)
    "$0" "$id" type "$1"
    until [ "$(turns)" -gt "$before" ]; do sleep 3; done
    tmux capture-pane -p -t "$pane" | grep -v '^[[:space:]]*$'
    ;;
  type)
    tmux send-keys -t "$pane" -l "$1"
    sleep 0.5
    tmux send-keys -t "$pane" Enter
    ;;
  key) tmux send-keys -t "$pane" "$@" ;;
  snap)
    mkdir -p "$here/$id/screens"
    tmux capture-pane -p -S - -t "$pane" > "$here/$id/screens/$1.txt"
    ;;
  show) tmux capture-pane -p -t "$pane" ;;
  *) echo "unknown command: $cmd" >&2; exit 2 ;;
esac
