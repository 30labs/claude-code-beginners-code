import asyncio
from pathlib import Path

import pytest
from mcp.server.mcpserver.exceptions import ToolError

from tally_mcp import server, spending

CSV = """date,description,amount
2026-08-01,Salary,3200.00
2026-08-02,Rent,-1450.00
2026-08-03,Corner Market,-82.40
2026-08-04,Night Market,-17.60
2026-08-05,Bookshop,-12.00
2026-09-04,Corner Market,-58.20
"""

RULES = """Market = "groceries"
Rent = "housing"
"""


@pytest.fixture
def files(tmp_path: Path) -> tuple[str, str]:
    csv_path = tmp_path / "bank.csv"
    csv_path.write_text(CSV, encoding="utf-8")
    rules_path = tmp_path / "rules.toml"
    rules_path.write_text(RULES, encoding="utf-8")
    return str(csv_path), str(rules_path)


def test_spending(files: tuple[str, str]) -> None:
    result = spending("2026-08", *files)
    assert result == {
        "housing": "1450.00",
        "groceries": "100.00",
        "uncategorised": "12.00",
    }
    assert list(result) == ["housing", "groceries", "uncategorised"]


def test_spending_empty_month(files: tuple[str, str]) -> None:
    assert spending("2026-07", *files) == {}


def test_spending_default_paths(
    files: tuple[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(Path(files[0]).parent)
    assert spending("2026-09") == {"groceries": "58.20"}


@pytest.mark.parametrize(
    ("month", "csv_name", "rules_name", "message"),
    [
        ("2026-13", "bank.csv", "rules.toml", "invalid month '2026-13'"),
        ("2026-08", "missing.csv", "rules.toml", "invalid bank CSV"),
        ("2026-08", "bank.csv", "missing.toml", "invalid rules file"),
    ],
)
def test_spending_bad_input(
    files: tuple[str, str], month: str, csv_name: str, rules_name: str, message: str
) -> None:
    folder = Path(files[0]).parent
    with pytest.raises(ToolError, match=message):
        spending(month, str(folder / csv_name), str(folder / rules_name))


def test_spending_via_server(files: tuple[str, str]) -> None:
    csv_path, rules_path = files
    args = {"month": "2026-09", "csv_path": csv_path, "rules_path": rules_path}
    result = asyncio.run(server.call_tool("spending", args))
    assert not result.is_error
    assert result.structured_content == {"groceries": "58.20"}


def test_spending_error_reaches_client(files: tuple[str, str]) -> None:
    # A ToolError keeps its message; any other exception would be hidden.
    with pytest.raises(ToolError, match="invalid month 'August'"):
        asyncio.run(server.call_tool("spending", {"month": "August"}))
