# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`tally` is a small Python CLI (Python ≥3.12, no runtime dependencies) that summarises a bank CSV export: money in, money out, net, optionally filtered to one month, optionally listing the largest expenses, and optionally grouping spending by category. Managed with `uv`; dev dependencies are pytest and ruff.

## Before calling a change done

Run all three and make sure they pass:

```sh
uv run ruff format .     # apply formatting (use --check to only verify)
uv run ruff check .      # lint; add --fix for auto-fixable issues
uv run pytest            # tests
```

## Commands

```sh
uv run pytest                                   # run all tests
uv run pytest test_ledger.py::test_cli_top      # run a single test
uv run pytest -k largest_expenses               # run tests matching a name
uv run python tally.py bank.csv                 # run the CLI against the sample data
uv run python tally.py bank.csv --month 2026-08 --top 3
uv run python tally.py bank.csv --rules rules.toml
```

Ruff runs with its default settings (no `[tool.ruff]` section in `pyproject.toml`), so the line length is 88. There is no build step.

## Architecture

Flat layout, two modules, no package:

- `ledger.py` — pure logic. `read_entries` parses the CSV (columns `date,description,amount`; ISO dates; signed amounts where negative = expense) into frozen `Entry` dataclasses. The other functions (`totals`, `in_month`, `largest_expenses`) are pure list transforms over `Entry`s. `read_rules` loads a flat TOML table of `word = "category"` (stdlib `tomllib`); `by_category` sums expenses per category, matching whole words case-insensitively with the first rule in file order winning, unmatched → `uncategorised`, ordered biggest spend first (ties by name).
- `tally.py` — the argparse CLI. `main(argv)` takes an explicit argv list and returns an exit code, which is how tests drive it. Argument validation lives in custom `type=` callables (`month_arg`, `count_arg`, `rules_arg`) that raise `argparse.ArgumentTypeError`, so bad input exits with code 2.
- `test_ledger.py` — tests for both modules. Each test writes a CSV string to `tmp_path`; CLI tests call `main([...])` and assert on `capsys` output.
- `bank.csv`, `rules.toml` — sample data for manual runs, not used by tests.

## Conventions

- Money is always `Decimal`, never float; `sum` calls pass `Decimal(0)` as the start value.
- `totals` returns both figures as positive amounts; `largest_expenses` returns entries with their original (negative) amounts and the CLI negates them for display.
- `largest_expenses` relies on `sorted` being stable so ties keep file order — this is tested.
- CLI output is fixed-width columns (`>10` for amounts, `<20` for descriptions); tests assert on exact lines, so formatting changes will break them.
