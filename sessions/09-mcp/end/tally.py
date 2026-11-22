"""tally: summarise a bank CSV export."""

import argparse
import tomllib
from datetime import date
from pathlib import Path

from ledger import (
    UNCATEGORISED,
    CsvError,
    Entry,
    by_category,
    in_category,
    in_month,
    largest_expenses,
    read_entries,
    read_rules,
    since,
    totals,
)


def month_arg(value: str) -> tuple[int, int]:
    """Parse YYYY-MM into (year, month)."""
    try:
        year, month = value.split("-")
        if len(year) != 4 or len(month) != 2:
            raise ValueError
        year_n, month_n = int(year), int(month)
        if not 1 <= month_n <= 12:
            raise ValueError
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"invalid month {value!r}, expected YYYY-MM"
        ) from None
    return year_n, month_n


def date_arg(value: str) -> date:
    """Parse YYYY-MM-DD into a date."""
    try:
        day = date.fromisoformat(value)
        # fromisoformat also takes forms like 20260901 and 2026-W36-1
        if day.isoformat() != value:
            raise ValueError
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"invalid date {value!r}, expected YYYY-MM-DD"
        ) from None
    return day


def count_arg(value: str) -> int:
    """Parse a positive integer."""
    try:
        n = int(value)
        if n < 1:
            raise ValueError
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"invalid count {value!r}, expected a positive integer"
        ) from None
    return n


def category_arg(value: str) -> str:
    """Parse a category name, which must not be blank."""
    if not value.strip():
        raise argparse.ArgumentTypeError(
            f"invalid category {value!r}, expected a category name"
        )
    return value


def rules_arg(value: str) -> dict[str, str]:
    """Load a rules TOML file mapping description words to categories."""
    try:
        return read_rules(Path(value))
    except (OSError, tomllib.TOMLDecodeError, TypeError, ValueError) as e:
        raise argparse.ArgumentTypeError(f"invalid rules file {value!r}: {e}") from None


def csv_arg(value: str) -> list[Entry]:
    """Load the entries of a bank CSV export."""
    try:
        return read_entries(Path(value))
    except (OSError, UnicodeDecodeError, CsvError) as e:
        raise argparse.ArgumentTypeError(f"invalid bank CSV {value!r}: {e}") from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tally")
    parser.add_argument("csv", type=csv_arg)
    parser.add_argument(
        "--month", type=month_arg, help="only count entries from YYYY-MM"
    )
    parser.add_argument(
        "--since",
        type=date_arg,
        metavar="YYYY-MM-DD",
        help="only count entries on or after this date",
    )
    parser.add_argument(
        "--top",
        type=count_arg,
        metavar="N",
        help="also list the N largest expenses, biggest first",
    )
    parser.add_argument(
        "--rules",
        type=rules_arg,
        metavar="PATH",
        help="also list spending per category, using word rules from a TOML file",
    )
    parser.add_argument(
        "--category",
        type=category_arg,
        metavar="NAME",
        help="only count entries in this category (needs --rules)",
    )
    args = parser.parse_args(argv)
    if args.category is not None:
        if args.rules is None:
            parser.error("--category needs --rules")
        known = {*args.rules.values(), UNCATEGORISED}
        if args.category not in known:
            parser.error(
                f"unknown category {args.category!r}, "
                f"expected one of: {', '.join(sorted(known))}"
            )
    entries = args.csv
    if args.month:
        entries = in_month(entries, *args.month)
    if args.since:
        entries = since(entries, args.since)
    if args.category is not None:
        entries = in_category(entries, args.rules, args.category)
    money_in, money_out = totals(entries)
    print(f"in   {money_in:>10}")
    print(f"out  {money_out:>10}")
    print(f"net  {money_in - money_out:>10}")
    if args.rules is not None:
        print()
        for category, spent in by_category(entries, args.rules).items():
            print(f"{category:<20} {spent:>10}")
    if args.top:
        print()
        for e in largest_expenses(entries, args.top):
            print(f"{e.day}  {e.description:<20} {-e.amount:>10}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
