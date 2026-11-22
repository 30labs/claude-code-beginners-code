"""Call a tool on an MCP server the way a client would."""

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import CallToolResult


async def call_each_month(
    server: MCPServer, tool: str, months: list[str]
) -> None:
    """Call `tool` once per month and print what comes back."""
    for month in months:
        try:
            args = {"month": month}
            result = await server.call_tool(tool, args)
        except ToolError as e:
            print(e)
            continue
        assert isinstance(result, CallToolResult)
        print(result.structured_content)
