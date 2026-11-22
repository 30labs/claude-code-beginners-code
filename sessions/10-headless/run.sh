#!/usr/bin/env bash
# The headless runs chapter 10 quotes, in order, in /tmp/tally.
# Each prints the command as the reader types it; the recording
# adds only the isolation flags record.sh uses.
set -uo pipefail
iso=(--setting-sources project,local --strict-mcp-config)
out=$(cd "$(dirname "$0")" && pwd)/runs
mkdir -p "$out"
cd /tmp/tally

run() {  # run <name> <claude args...>
  local name=$1; shift
  printf '$ claude' > "$out/$name.txt"
  printf ' %q' "$@" >> "$out/$name.txt"
  printf '\n' >> "$out/$name.txt"
  claude "${iso[@]}" "$@" >> "$out/$name.txt" 2>&1
  echo "exit=$?" >> "$out/$name.txt"
}

run 1-text -p "Run the tests. Reply with one line: how many passed."
run 2-json -p "Run the tests. Reply with one line: how many passed." \
  --output-format json
run 3-denied -p "When a filter leaves no income, tally prints 'in 0' instead of 'in 0.00'. Fix it with a test." \
  --output-format json
git stash -u -q 2>/dev/null; git stash drop -q 2>/dev/null
run 4-accept -p "When a filter leaves no income, tally prints 'in 0' instead of 'in 0.00'. Fix it with a test." \
  --permission-mode acceptEdits
git diff --stat > "$out/4-accept.diffstat"
git diff > "$out/diff-for-review.patch"
{ echo '$ git diff | claude -p "Review this diff. List real problems only, most serious first."'
  git diff | claude "${iso[@]}" -p "Review this diff. List real problems only, most serious first."
  echo "exit=$?"; } > "$out/5-review.txt" 2>&1
