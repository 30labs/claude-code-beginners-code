from decimal import Decimal
from pathlib import Path

import pytest

from ledger import in_month, largest_expenses, read_entries, totals
from tally import main

CSV = """date,description,amount
2026-08-01,Salary,3200.00
2026-08-02,Rent,-1450.00
2026-08-03,Corner Market,-82.40
2026-09-01,Salary,3100.00
2026-09-04,Corner Market,-58.20
"""


def test_totals(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    money_in, money_out = totals(read_entries(path))
    assert money_in == Decimal("6300.00")
    assert money_out == Decimal("1590.60")


def test_in_month(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    entries = in_month(read_entries(path), 2026, 9)
    assert [e.description for e in entries] == ["Salary", "Corner Market"]
    assert totals(entries) == (Decimal("3100.00"), Decimal("58.20"))


def test_in_month_ignores_same_month_other_year(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV + "2025-08-15,Old,-10.00\n", encoding="utf-8")
    entries = in_month(read_entries(path), 2026, 8)
    assert len(entries) == 3


def test_cli_month(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    assert main([str(path), "--month", "2026-08"]) == 0
    out = capsys.readouterr().out.split("\n")
    assert out[0].split() == ["in", "3200.00"]
    assert out[1].split() == ["out", "1532.40"]
    assert out[2].split() == ["net", "1667.60"]


@pytest.mark.parametrize("bad", ["2026-13", "2026-8", "Aug", "2026/08", "2026-00"])
def test_cli_month_rejects_bad_value(tmp_path: Path, bad: str) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        main([str(path), "--month", bad])
    assert exc.value.code == 2


def test_largest_expenses(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    top = largest_expenses(read_entries(path), 2)
    assert [(e.description, e.amount) for e in top] == [
        ("Rent", Decimal("-1450.00")),
        ("Corner Market", Decimal("-82.40")),
    ]


def test_largest_expenses_skips_income_and_caps_at_available(
    tmp_path: Path,
) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    top = largest_expenses(read_entries(path), 10)
    assert [e.amount for e in top] == [
        Decimal("-1450.00"),
        Decimal("-82.40"),
        Decimal("-58.20"),
    ]


def test_largest_expenses_ties_keep_file_order(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(
        "date,description,amount\n2026-08-01,First,-20.00\n2026-08-02,Second,-20.00\n",
        encoding="utf-8",
    )
    top = largest_expenses(read_entries(path), 2)
    assert [e.description for e in top] == ["First", "Second"]


def test_cli_top(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    assert main([str(path), "--top", "2"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 6
    assert lines[3] == ""
    assert lines[4].split() == ["2026-08-02", "Rent", "1450.00"]
    assert lines[5].split() == ["2026-08-03", "Corner", "Market", "82.40"]


def test_cli_top_with_month(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    assert main([str(path), "--month", "2026-09", "--top", "5"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[4:] == ["2026-09-04  Corner Market             58.20"]


def test_cli_without_top_prints_only_totals(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    assert main([str(path)]) == 0
    assert len(capsys.readouterr().out.splitlines()) == 3


@pytest.mark.parametrize("bad", ["0", "-1", "two", "1.5"])
def test_cli_top_rejects_bad_value(tmp_path: Path, bad: str) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        main([str(path), "--top", bad])
    assert exc.value.code == 2
