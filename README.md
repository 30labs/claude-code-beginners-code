# First Steps with Claude Code: code and sessions

This repository holds the sample project from the book *First Steps with Claude Code* and every recorded session the book quotes.

- `tally/` is the project as the last chapter leaves it: the ledger, its command-line tool, the MCP server, the tests, `CLAUDE.md`, the permission rules, the skill and the subagent. Run `uv sync` and then `uv run pytest` inside it.
- `sessions/` holds each session in full. `<session>/end/` is the project when the session ended, `diff.patch` is what the session changed, and `screens/` has the uncut terminal captures the book excerpts. Each session starts from the `end/` of the session named in its `from` file, plus any files in its `add/` folder. `sessions/README.md` explains how they were recorded.

## Sessions by chapter

- `00-start` — the project you build by hand in chapter 1.
- `01-first-run` — chapter 1, a first question.
- `02-first-change` — chapter 2, a first change.
- `03-manual` — chapter 3, permissions.
- `04-claude-md` — chapter 4, CLAUDE.md.
- `05-plan` — chapter 5, plan mode (with both versions of the plan).
- `06-context` — chapter 6, context.
- `07-debug` — chapter 7, debugging.
- `08-skill` — chapter 8, skills.
- `09-mcp` — chapter 9, MCP and subagents.
- `10-headless` — chapter 10, headless runs (`runs/` holds the output of `run.sh`).

The code is released under the MIT License (see `LICENSE`).

Claude and Claude Code are trademarks of Anthropic, PBC. This repository is independent and is not affiliated with, endorsed by, or sponsored by Anthropic.
