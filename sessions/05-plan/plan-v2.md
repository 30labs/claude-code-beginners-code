# Plan: spending by category (tests first)

## Context
`tally` currently reports only in/out/net and the largest expenses. The user wants spending grouped by category, where categories come from a `rules.toml` file mapping a word in the description to a category (e.g. `Market` → `groceries`); unmatched expenses are `uncategorised`. Tests are written first and must fail before the implementation lands.

Decisions (confirmed with user):
- Match = **whole word, case-insensitive** ("Market" matches "Corner Market"/"corner market", "Rent" does not match "Parental").
- CLI opt-in via **`--rules PATH`**; without it output is unchanged.

Further defaults (mine, easy to change):
- Only expenses (amount < 0) are grouped — it's "spending"; income such as "Refund Bookshop" is ignored, like `largest_expenses`.
- If several rules match, the **first rule in file order** wins (`tomllib` preserves order).
- Words are the description split on whitespace; rule keys compared with `casefold()`.
- Output order (user request): **biggest spend first** — all categories, `uncategorised` included, sorted by total descending; ties broken by name. `uncategorised` only appears if something is unmatched.
- Parsed with stdlib `tomllib` — still no runtime dependencies.

## rules.toml format
Flat top-level table, word → category:
```toml
Market = "groceries"
Rent = "housing"
Metro = "transport"
```
Rejected (exit code 2): missing/unreadable file, invalid TOML, a non-string value, a key containing whitespace (can never match a single word).

## Step 1 — tests (`test_ledger.py`), run and confirm they fail
Follow the existing pattern: write CSV/TOML strings to `tmp_path`, CLI tests call `main([...])` and use `capsys`.

Pure logic (`ledger.py`):
- `test_read_rules` — parses the table into a `dict[str, str]` in file order.
- `test_by_category` — `Rent`→housing, both `Corner Market` rows summed into groceries (positive `Decimal`s), income excluded.
- `test_by_category_unmatched_is_uncategorised`
- `test_by_category_matches_whole_word_any_case` — `market` rule matches "Corner MARKET"; `Rent` rule does not match "Parental leave".
- `test_by_category_first_rule_wins` — description matching two rules goes to the rule listed first.
- `test_by_category_ignores_income`

CLI (`tally.py`):
- `test_cli_rules` — exact lines after a blank line, e.g. `"housing                 1450.00"` (`<20` / `>10`).
- `test_cli_rules_with_month` — breakdown respects `--month`.
- `test_cli_rules_biggest_spend_first` — lines are in descending total order, with `uncategorised` sorted among them by its total (not pinned last).
- `test_by_category_ties_sorted_by_name` — equal totals come out alphabetically.
- `test_cli_rules_and_top` — both sections present, in a fixed order (totals, blank, categories, blank, top).
- `test_cli_without_rules_prints_only_totals` — existing test already covers this; keep.
- `test_cli_rules_rejects_bad_file` (parametrised: missing file, invalid TOML, non-string value, key with space) → `SystemExit` code 2.

## Step 2 — implementation
`ledger.py`:
- `read_rules(path: Path) -> dict[str, str]` — `tomllib.load` (binary mode), validate values are `str` and keys have no whitespace, raise `ValueError` otherwise.
- `UNCATEGORISED = "uncategorised"`
- `categorise(description: str, rules: dict[str, str]) -> str` — casefold description words into a set; return the category of the first rule whose casefolded key is in it, else `UNCATEGORISED`.
- `by_category(entries, rules) -> dict[str, Decimal]` — expenses only, positive totals, `Decimal(0)` start values; returns the dict already ordered biggest spend first (total desc, then name asc) so the CLI just prints it.

`tally.py`:
- `rules_arg(value: str) -> dict[str, str]` — calls `read_rules(Path(value))`, converts `OSError`/`tomllib.TOMLDecodeError`/`ValueError` to `argparse.ArgumentTypeError` (same pattern as `month_arg`/`count_arg`) → exit 2.
- `--rules` option with `metavar="PATH"` and help text; after the totals, if given, print a blank line then `f"{category:<20} {total:>10}"` per category. Printed before the `--top` section.

Also: add a sample `rules.toml` next to `bank.csv` for manual runs; update CLAUDE.md (architecture/commands) to mention `read_rules`/`by_category`, `--rules` and the sample file.

## Verification
1. After Step 1: `uv run pytest` — new tests fail (ImportError / missing option), old ones still pass.
2. After Step 2: `uv run ruff format .`, `uv run ruff check .`, `uv run pytest` all pass.
3. Manual: `uv run python tally.py bank.csv --rules rules.toml` and `... --month 2026-08 --rules rules.toml --top 3` — check groceries = 217.60 for August (82.40 + 61.15 + 74.05) and Electricity shows under its category or uncategorised as expected.
