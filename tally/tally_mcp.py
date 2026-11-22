"""tally as an MCP server: spending by category, over stdio."""

import argparse

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from ledger import by_category, in_month
from tally import csv_arg, month_arg, rules_arg

server = MCPServer("tally")


@server.tool()
def spending(
    month: str, csv_path: str = "bank.csv", rules_path: str = "rules.toml"
) -> dict[str, str]:
    """Return spending per category for a month (YYYY-MM), biggest first.

    Amounts are positive decimal strings. Relative paths are resolved against
    the server's working directory.
    """
    try:
        year, month_n = month_arg(month)
        entries = csv_arg(csv_path)
        rules = rules_arg(rules_path)
    except argparse.ArgumentTypeError as e:
        raise ToolError(str(e)) from None
    spent = by_category(in_month(entries, year, month_n), rules)
    return {category: str(amount) for category, amount in spent.items()}


if __name__ == "__main__":
    server.run()
