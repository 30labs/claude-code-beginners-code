import asyncio

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from mcp_server_calls import call_each_month

server = MCPServer("demo")


@server.tool()
def check(month: str) -> str:
    """Accept a month written as YYYY-MM."""
    if month == "bad":
        raise ToolError("invalid month 'bad'")
    if month == "boom":
        raise ValueError("a detail the client never sees")
    return f"ok {month}"


months = ["2026-09", "bad", "boom"]
asyncio.run(call_each_month(server, "check", months))
