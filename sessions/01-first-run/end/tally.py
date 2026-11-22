"""tally: summarise a bank CSV export."""

import argparse
from pathlib import Path

from ledger import read_entries, totals


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tally")
    parser.add_argument("csv", type=Path)
    args = parser.parse_args(argv)
    money_in, money_out = totals(read_entries(args.csv))
    print(f"in   {money_in:>10}")
    print(f"out  {money_out:>10}")
    print(f"net  {money_in - money_out:>10}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
