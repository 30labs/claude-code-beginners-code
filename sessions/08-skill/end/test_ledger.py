from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from ledger import (
    by_category,
    in_category,
    in_month,
    largest_expenses,
    read_entries,
    read_rules,
    since,
    totals,
)
from tally import main

CSV = """date,description,amount
2026-08-01,Salary,3200.00
2026-08-02,Rent,-1450.00
2026-08-03,Corner Market,-82.40
2026-09-01,Salary,3100.00
2026-09-04,Corner Market,-58.20
"""

RULES = """Market = "groceries"
Rent = "housing"
"""


def test_totals(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    money_in, money_out = totals(read_entries(path))
    assert money_in == Decimal("6300.00")
    assert money_out == Decimal("1590.60")


def test_read_entries_with_bom_and_crlf(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_bytes(b"\xef\xbb\xbf" + CSV.replace("\n", "\r\n").encode("utf-8"))
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


def test_since_includes_the_day_itself(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    entries = since(read_entries(path), date(2026, 8, 3))
    assert [e.day for e in entries] == [
        date(2026, 8, 3),
        date(2026, 9, 1),
        date(2026, 9, 4),
    ]


def test_cli_since(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    assert main([str(path), "--since", "2026-08-03"]) == 0
    out = capsys.readouterr().out.split("\n")
    assert out[0].split() == ["in", "3100.00"]
    assert out[1].split() == ["out", "140.60"]
    assert out[2].split() == ["net", "2959.40"]


def test_cli_since_with_month(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    assert main([str(path), "--month", "2026-08", "--since", "2026-08-02"]) == 0
    out = capsys.readouterr().out.split("\n")
    assert out[0].split() == ["in", "0"]
    assert out[1].split() == ["out", "1532.40"]
    assert out[2].split() == ["net", "-1532.40"]


@pytest.mark.parametrize(
    "bad",
    ["2026-13-01", "2026-02-30", "2026-9-1", "01/09/2026", "20260901", "2026-W36-1"],
)
def test_cli_since_rejects_bad_value(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], bad: str
) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        main([str(path), "--since", bad])
    assert exc.value.code == 2
    assert f"invalid date {bad!r}, expected YYYY-MM-DD" in capsys.readouterr().err


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


def test_read_rules(tmp_path: Path) -> None:
    path = tmp_path / "rules.toml"
    path.write_text(RULES, encoding="utf-8")
    assert list(read_rules(path).items()) == [
        ("Market", "groceries"),
        ("Rent", "housing"),
    ]


def test_by_category(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    rules = {"Market": "groceries", "Rent": "housing"}
    assert list(by_category(read_entries(path), rules).items()) == [
        ("housing", Decimal("1450.00")),
        ("groceries", Decimal("140.60")),
    ]


def test_by_category_unmatched_is_uncategorised(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    assert by_category(read_entries(path), {"Rent": "housing"}) == {
        "housing": Decimal("1450.00"),
        "uncategorised": Decimal("140.60"),
    }


def test_by_category_matches_whole_word_any_case(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(
        "date,description,amount\n"
        "2026-08-01,Corner MARKET,-10.00\n"
        "2026-08-02,Parental leave,-5.00\n",
        encoding="utf-8",
    )
    rules = {"market": "groceries", "Rent": "housing"}
    assert by_category(read_entries(path), rules) == {
        "groceries": Decimal("10.00"),
        "uncategorised": Decimal("5.00"),
    }


def test_by_category_first_rule_wins(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(
        "date,description,amount\n2026-08-01,Market Cafe,-10.00\n",
        encoding="utf-8",
    )
    rules = {"Cafe": "eating out", "Market": "groceries"}
    assert by_category(read_entries(path), rules) == {"eating out": Decimal("10.00")}


def test_by_category_ignores_income(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(
        "date,description,amount\n2026-08-20,Refund Bookshop,18.90\n",
        encoding="utf-8",
    )
    assert by_category(read_entries(path), {"Bookshop": "books"}) == {}


def test_by_category_ties_sorted_by_name(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(
        "date,description,amount\n2026-08-01,First,-20.00\n2026-08-02,Second,-20.00\n",
        encoding="utf-8",
    )
    rules = {"First": "zeta", "Second": "alpha"}
    assert list(by_category(read_entries(path), rules)) == ["alpha", "zeta"]


def test_cli_rules(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    rules = tmp_path / "rules.toml"
    rules.write_text(RULES, encoding="utf-8")
    assert main([str(path), "--rules", str(rules)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[3:] == [
        "",
        "housing                 1450.00",
        "groceries                140.60",
    ]


def test_cli_rules_with_month(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    rules = tmp_path / "rules.toml"
    rules.write_text(RULES, encoding="utf-8")
    assert main([str(path), "--month", "2026-09", "--rules", str(rules)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[3:] == ["", "groceries                 58.20"]


def test_cli_rules_biggest_spend_first(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV + "2026-08-10,Plumber,-200.00\n", encoding="utf-8")
    rules = tmp_path / "rules.toml"
    rules.write_text(RULES, encoding="utf-8")
    assert main([str(path), "--rules", str(rules)]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert [line.split()[0] for line in lines[4:]] == [
        "housing",
        "uncategorised",
        "groceries",
    ]


def test_cli_rules_and_top(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    rules = tmp_path / "rules.toml"
    rules.write_text(RULES, encoding="utf-8")
    assert main([str(path), "--rules", str(rules), "--top", "1"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[3:] == [
        "",
        "housing                 1450.00",
        "groceries                140.60",
        "",
        "2026-08-02  Rent                    1450.00",
    ]


def test_in_category_keeps_income_and_expenses(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV + "2026-08-20,Refund Market,5.00\n", encoding="utf-8")
    rules = {"Market": "groceries", "Rent": "housing"}
    entries = in_category(read_entries(path), rules, "groceries")
    assert [e.amount for e in entries] == [
        Decimal("-82.40"),
        Decimal("-58.20"),
        Decimal("5.00"),
    ]


def test_in_category_uncategorised(tmp_path: Path) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    entries = in_category(read_entries(path), {"Rent": "housing"}, "uncategorised")
    assert [e.description for e in entries] == [
        "Salary",
        "Corner Market",
        "Salary",
        "Corner Market",
    ]


def test_cli_category(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    rules = tmp_path / "rules.toml"
    rules.write_text(RULES, encoding="utf-8")
    assert main([str(path), "--rules", str(rules), "--category", "groceries"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert [line.split() for line in lines[:3]] == [
        ["in", "0"],
        ["out", "140.60"],
        ["net", "-140.60"],
    ]
    assert lines[3:] == ["", "groceries                140.60"]


def test_cli_category_with_month(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    rules = tmp_path / "rules.toml"
    rules.write_text(RULES, encoding="utf-8")
    argv = [str(path), "--month", "2026-09", "--rules", str(rules)]
    assert main([*argv, "--category", "groceries", "--top", "5"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[1].split() == ["out", "58.20"]
    assert lines[3:] == [
        "",
        "groceries                 58.20",
        "",
        "2026-09-04  Corner Market             58.20",
    ]


def test_cli_category_uncategorised(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    rules = tmp_path / "rules.toml"
    rules.write_text(RULES, encoding="utf-8")
    assert main([str(path), "--rules", str(rules), "--category", "uncategorised"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert [line.split() for line in lines] == [
        ["in", "6300.00"],
        ["out", "0"],
        ["net", "6300.00"],
        [],
    ]


@pytest.mark.parametrize(
    ("bad", "with_rules", "message"),
    [
        ("", True, "invalid category ''"),
        ("   ", True, "invalid category '   '"),
        ("grocery", True, "unknown category 'grocery'"),
        ("Groceries", True, "unknown category 'Groceries'"),
        ("groceries", False, "--category needs --rules"),
    ],
    ids=["empty", "blank", "unknown", "wrong-case", "without-rules"],
)
def test_cli_category_rejects_bad_value(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    bad: str,
    with_rules: bool,
    message: str,
) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    rules = tmp_path / "rules.toml"
    rules.write_text(RULES, encoding="utf-8")
    argv = [str(path), "--category", bad]
    if with_rules:
        argv += ["--rules", str(rules)]
    with pytest.raises(SystemExit) as exc:
        main(argv)
    assert exc.value.code == 2
    assert message in capsys.readouterr().err


@pytest.mark.parametrize(
    "bad",
    [
        None,
        "Market = groceries\n",
        "Market = 3\n",
        '"Corner Market" = "groceries"\n',
        '[shops]\nMarket = "groceries"\n',
    ],
    ids=["missing", "invalid-toml", "non-string", "key-with-space", "nested-table"],
)
def test_cli_rules_rejects_bad_file(tmp_path: Path, bad: str | None) -> None:
    path = tmp_path / "bank.csv"
    path.write_text(CSV, encoding="utf-8")
    rules = tmp_path / "rules.toml"
    if bad is not None:
        rules.write_text(bad, encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        main([str(path), "--rules", str(rules)])
    assert exc.value.code == 2


@pytest.mark.parametrize(
    ("bad", "message"),
    [
        (None, "No such file"),
        (b"", "missing column(s): date, description, amount"),
        (b"day,description,amount\n", "missing column(s): date"),
        (b'date,description,amount\n2026-09-01,Salary,"1,234.00"\n', "'1,234.00'"),
        (b"date,description,amount\n2026-09-01,Salary,1,234.00\n", "too many"),
        (b"date,description,amount\n2026-09-01,Salary\n", "line 2: too few"),
        (b"date,description,amount\n01/09/2026,Salary,1.00\n", "invalid date"),
        (b"date,description,amount\n2026-09-01,Salary,\n", "invalid amount ''"),
        (b"date,description,amount\n2026-09-01,Salary,NaN\n", "invalid amount"),
        (b"date,description,amount\n2026-09-01,Caf\xe9,-3.50\n", "utf-8"),
        (b'date,description,amount\n2026-09-01,"Salary,1.00\n', "too few"),
        (b'date,description,amount\n2026-09-01,"' + b"x" * 200_000, "field limit"),
    ],
    ids=[
        "missing",
        "empty",
        "wrong-header",
        "quoted-thousands",
        "unquoted-thousands",
        "short-row",
        "bad-date",
        "blank-amount",
        "nan-amount",
        "not-utf8",
        "unclosed-quote",
        "huge-field",
    ],
)
def test_cli_rejects_bad_csv(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    bad: bytes | None,
    message: str,
) -> None:
    path = tmp_path / "bank.csv"
    if bad is not None:
        path.write_bytes(bad)
    with pytest.raises(SystemExit) as exc:
        main([str(path)])
    assert exc.value.code == 2
    err = capsys.readouterr().err
    assert "invalid bank CSV" in err
    assert message in err
