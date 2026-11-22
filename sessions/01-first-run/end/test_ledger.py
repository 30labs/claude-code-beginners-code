from decimal import Decimal
from pathlib import Path

from ledger import read_entries, totals

CSV = """date,description,amount
2026-08-01,Salary,3200.00
2026-08-02,Rent,-1450.00
2026-08-03,Corner Market,-82.40
"""


def test_totals(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    money_in, money_out = totals(read_entries(path))
    assert money_in == Decimal("3200.00")
    assert money_out == Decimal("1532.40")
