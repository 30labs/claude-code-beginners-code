#!/usr/bin/env bash
# Record one agent session the book quotes.
#
#   sessions/record.sh <id>            headless: claude -p, stream-json
#   sessions/record.sh <id> --tui      interactive: a tmux pane to drive
#   sessions/record.sh <id> --finish <work tree>   after a --tui run
#
# <id>/from       the session whose end/ state this one starts from
# <id>/prompt.txt the prompt (headless)
# <id>/flags      extra claude flags, one line (optional)
#
# Writes <id>/stream.jsonl (headless), <id>/diff.patch and <id>/end/.
# User settings, user CLAUDE.md and MCP servers outside the project are
# left out, so the session sees only what a reader's project holds.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
id=$1
mode=${2:-}
dir=$here/$id

finish() {
  git -C "$work" add -A
  start=$(git -C "$work" rev-list --max-parents=0 HEAD)
  git -C "$work" diff --cached "$start" > "$dir/diff.patch"
  rm -rf "$dir/end"
  mkdir -p "$dir/end"
  git -C "$work" ls-files -z |
    (cd "$work" && xargs -0 cp --parents -t "$dir/end")
  echo "work tree: $work"
}

if [ "$mode" = --finish ]; then
  work=$3
  finish
  exit 0
fi

from=$(cat "$dir/from")
flags=$(cat "$dir/flags" 2>/dev/null || true)

# One fixed path, so screens name the same folder in every session.
work=/tmp/tally
rm -rf "$work"
mkdir -p "$work"
cp -a "$here/$from/end/." "$work/"
# <id>/add/ holds files the reader brings in before the session.
if [ -d "$dir/add" ]; then cp -a "$dir/add/." "$work/"; fi
git -C "$work" init -q
git -C "$work" config user.name Reader
git -C "$work" config user.email reader@example.com
git -C "$work" add -A
git -C "$work" commit -qm "start"
(cd "$work" && uv sync -q)

base=(--setting-sources project,local --strict-mcp-config)

if [ "$mode" = --tui ]; then
  name="tally-$id"
  # shellcheck disable=SC2086
  tmux new-session -d -s "$name" -x 64 -y 40 -c "$work" \
    "claude ${base[*]} $flags; exec bash"
  echo "tmux session $name in $work"
  echo "drive it with sessions/tui.sh; then: sessions/record.sh $id --finish $work"
  exit 0
fi

# shellcheck disable=SC2086
(cd "$work" && claude -p "$(cat "$dir/prompt.txt")" "${base[@]}" $flags \
  --output-format stream-json --verbose) > "$dir/stream.jsonl"
finish
