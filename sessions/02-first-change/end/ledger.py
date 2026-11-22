"""Read a bank CSV export and add it up."""

import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class Entry:
    day: date
    description: str
    amount: Decimal


def read_entries(path: Path) -> list[Entry]:
    with path.open(newline="", encoding="utf-8") as f:
        return [
            Entry(
                day=date.fromisoformat(row["date"]),
                description=row["description"].strip(),
                amount=Decimal(row["amount"]),
            )
            for row in csv.DictReader(f)
        ]


def totals(entries: list[Entry]) -> tuple[Decimal, Decimal]:
    """Return (money in, money out) as positive amounts."""
    money_in = sum(
        (e.amount for e in entries if e.amount > 0), Decimal(0)
    )
    money_out = sum(
        (-e.amount for e in entries if e.amount < 0), Decimal(0)
    )
    return money_in, money_out


def in_month(entries: list[Entry], year: int, month: int) -> list[Entry]:
    """Return only the entries dated in the given month."""
    return [e for e in entries if e.day.year == year and e.day.month == month]
