"""tally: summarise a bank CSV export."""

import argparse
from pathlib import Path

from ledger import in_month, read_entries, totals


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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tally")
    parser.add_argument("csv", type=Path)
    parser.add_argument(
        "--month", type=month_arg, help="only count entries from YYYY-MM"
    )
    args = parser.parse_args(argv)
    entries = read_entries(args.csv)
    if args.month:
        entries = in_month(entries, *args.month)
    money_in, money_out = totals(entries)
    print(f"in   {money_in:>10}")
    print(f"out  {money_out:>10}")
    print(f"net  {money_in - money_out:>10}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
