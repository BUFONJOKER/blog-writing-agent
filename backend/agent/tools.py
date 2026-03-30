import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from config import Config
from typing import Literal

async def get_local_mcp_tools() -> list:
    """Fetch tool definitions from the local MCP server over stdio.

    Returns:
        list: Tool objects discovered from the local MCP server.
    """
    mcp_server_config = {
        "blog-research-tools": {
            "transport": "stdio",
            "command": "uv",
            "args": [
                "run",
                "--project",
                r"D:\blog-writing-agent\mcp_server",
                "python",
                r"D:\blog-writing-agent\mcp_server\server.py",
            ],
        }
    }

    client = MultiServerMCPClient(mcp_server_config)
    return await client.get_tools()


async def get_hosted_mcp_tools() -> list:
    """Fetch tool definitions from the hosted MCP server over HTTP.

    Returns:
        list: Tool objects discovered from the hosted MCP server.
    """
    mcp_server_config = {
        "blog-research-tools (Hosted)": {
            "url": "https://Blog-Research-Tools.fastmcp.app/mcp",
            "transport": "streamable_http",
            "headers": {
                "Authorization": f"Bearer {Config.HORIZON_TOKEN}",
            },
        }
    }

    client = MultiServerMCPClient(mcp_server_config)
    return await client.get_tools()


async def initialize_tools(tools_place: Literal['hosted', 'local']) -> list:
    """Load local or hosted MCP tools according to given tool place and print a readable summary for debugging and return the list of tools."""
    if tools_place == 'hosted':
        tools = await get_hosted_mcp_tools()
    else:
        tools = await get_local_mcp_tools()

    # print(f"Discovered {len(tools)} tools from MCP server ({tools_place}):")
    # for tool in tools:
    #     print(f"- {tool.name}")

    return tools


if __name__ == "__main__":
    asyncio.run(initialize_tools('local'))