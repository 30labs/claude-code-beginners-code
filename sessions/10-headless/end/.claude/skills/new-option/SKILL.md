---
description: Add a command-line option to tally, tests first.
  Use when asked to add a flag or option to the CLI.
argument-hint: <--flag> <what it does>
---

Add this option to tally: $ARGUMENTS

Uncommitted changes right now:
!`git status --short`

1. Read tally.py and follow the pattern the existing options
   use: a `type=` function that raises
   `argparse.ArgumentTypeError`, so a bad value exits with
   code 2.
2. Write the tests first: the normal case, the option together
   with --month, and at least three bad values. Run them and
   show that they fail.
3. Implement it. Logic goes in ledger.py, output in tally.py.
4. Run `uv run ruff format .`, `uv run ruff check .` and
   `uv run pytest`. All three must pass.
5. Run the new option on bank.csv, show the output, and stop.
   Do not commit.
