"""Read a bank CSV export and add it up."""

import csv
import tomllib
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

UNCATEGORISED = "uncategorised"


@dataclass(frozen=True)
class Entry:
    day: date
    description: str
    amount: Decimal


class CsvError(ValueError):
    """A bank CSV that cannot be read, with the line it went wrong on."""


COLUMNS = ("date", "description", "amount")


def read_entries(path: Path) -> list[Entry]:
    """Read entries from a CSV; raise CsvError on any malformed content."""
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        try:
            missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
            if missing:
                raise CsvError(f"missing column(s): {', '.join(missing)}")
            return [parse_row(row, reader.line_num) for row in reader]
        except csv.Error as e:
            raise CsvError(f"line {reader.line_num}: {e}") from None


def parse_row(row: dict[str | None, str | None], line: int) -> Entry:
    """Turn one CSV row into an Entry; raise CsvError if it is malformed."""
    if None in row:
        raise CsvError(f"line {line}: too many fields")
    if any(row[c] is None for c in COLUMNS):
        raise CsvError(f"line {line}: too few fields")
    try:
        day = date.fromisoformat(row["date"])
    except ValueError:
        raise CsvError(f"line {line}: invalid date {row['date']!r}") from None
    try:
        amount = Decimal(row["amount"])
    except InvalidOperation:
        amount = None
    if amount is None or not amount.is_finite():
        raise CsvError(f"line {line}: invalid amount {row['amount']!r}")
    return Entry(day=day, description=row["description"].strip(), amount=amount)


def totals(entries: list[Entry]) -> tuple[Decimal, Decimal]:
    """Return (money in, money out) as positive amounts."""
    money_in = sum((e.amount for e in entries if e.amount > 0), Decimal(0))
    money_out = sum((-e.amount for e in entries if e.amount < 0), Decimal(0))
    return money_in, money_out


def in_month(entries: list[Entry], year: int, month: int) -> list[Entry]:
    """Return only the entries dated in the given month."""
    return [e for e in entries if e.day.year == year and e.day.month == month]


def since(entries: list[Entry], day: date) -> list[Entry]:
    """Return only the entries dated on or after the given day."""
    return [e for e in entries if e.day >= day]


def largest_expenses(entries: list[Entry], n: int) -> list[Entry]:
    """Return the n biggest expenses, biggest first; ties keep file order."""
    expenses = [e for e in entries if e.amount < 0]
    return sorted(expenses, key=lambda e: e.amount)[:n]


def read_rules(path: Path) -> dict[str, str]:
    """Read a TOML table mapping a description word to a category."""
    with path.open("rb") as f:
        rules = tomllib.load(f)
    for word, category in rules.items():
        if not isinstance(category, str):
            raise TypeError(f"category for {word!r} must be a string")
        if len(word.split()) != 1:
            raise ValueError(f"rule {word!r} must be a single word")
    return rules


def categorise(description: str, rules: dict[str, str]) -> str:
    """Return the category of the first rule whose word is in the description."""
    words = {w.casefold() for w in description.split()}
    for word, category in rules.items():
        if word.casefold() in words:
            return category
    return UNCATEGORISED


def in_category(
    entries: list[Entry], rules: dict[str, str], category: str
) -> list[Entry]:
    """Return only the entries whose description falls in the given category."""
    return [e for e in entries if categorise(e.description, rules) == category]


def by_category(entries: list[Entry], rules: dict[str, str]) -> dict[str, Decimal]:
    """Return spending per category as positive amounts, biggest first."""
    spent: dict[str, Decimal] = {}
    for e in entries:
        if e.amount < 0:
            category = categorise(e.description, rules)
            spent[category] = spent.get(category, Decimal(0)) - e.amount
    return dict(sorted(spent.items(), key=lambda item: (-item[1], item[0])))
