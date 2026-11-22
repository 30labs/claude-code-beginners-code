# Recorded sessions

Every agent session the book quotes is a real run of the pinned `claude` against the sample
project `tally`, recorded here so the fact-check pass can compare each excerpt with what happened.

- `00-start/end/` is the project the reader starts from. Each later session starts from the
  `end/` of the session named in its `from` file, plus any files in its `add/` folder (files the
  reader brings in, such as a new bank export).
- `record.sh <id>` runs a headless session from `prompt.txt`; `record.sh <id> --tui` opens an
  interactive session in a 64-column tmux pane, driven with `tui.sh`, and `--finish` saves
  `diff.patch` (against the session's start) and `end/`.
- `screens/` holds full-scrollback captures of the interactive pane, numbered in the order they
  were taken. `10-headless/runs/` holds the headless runs chapter 10 quotes, made by its `run.sh`.
- Plan-mode plans are saved as `05-plan/plan-v1.md` and `plan-v2.md`, before and after feedback.

Recording setup: sessions run in `/tmp/tally`, a fresh git repository per session, with
`--setting-sources project,local --strict-mcp-config` so nothing from the recording machine's own
settings, CLAUDE.md or MCP servers reaches the session. Chapter 9's second part drops
`--strict-mcp-config` so the project's `.mcp.json` loads, and sets
`ENABLE_CLAUDEAI_MCP_SERVERS=false` instead. The account was a Claude Max plan; the model was the
account default. The login name and home directory in shell prompts are replaced with
`reader@host` and `/home/reader`; nothing else in a capture is edited.
