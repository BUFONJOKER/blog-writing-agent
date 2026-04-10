import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from agent.config import HORIZON_TOKEN
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
                r"D:\llm-projects\blog-writing-agent\mcp_server",
                "python",
                r"D:\llm-projects\blog-writing-agent\mcp_server\server.py",
            ],
        }
    }

    client = MultiServerMCPClient(mcp_server_config)
    return await client.get_tools()


async def get_hosted_horizon_mcp_tools() -> list:
    """Fetch tool definitions from the hosted MCP server over HTTP.

    Returns:
        list: Tool objects discovered from the hosted MCP server.
    """
    mcp_server_config = {
        "blog-research-tools (Hosted)": {
            "url": "https://Blog-Research-Tools.fastmcp.app/mcp",
            "transport": "streamable_http",
            "headers": {
                "Authorization": f"Bearer {HORIZON_TOKEN}",
            },
        }
    }

    mcp_server_config_hf = {
        "blog-research-tools-hf": {
            # Use the /sse suffix shown in your logs
            "url": "https://bufon-joker-blog-writing-agent-mcp-server-v2.hf.space/sse",
            # Change from 'streamable_http' to 'sse'
            "transport": "sse",
        }
    }

    client = MultiServerMCPClient(mcp_server_config)
    return await client.get_tools()

async def get_hosted_huggingface_mcp_tools() -> list:
    """Fetch tool definitions from the hosted MCP server over HTTP.

    Returns:
        list: Tool objects discovered from the hosted MCP server.
    """

    mcp_server_config_hf = {
        "blog-research-tools-hf": {
            # Use the /sse suffix shown in your logs
            "url": "https://bufon-joker-blog-writing-agent-mcp-server-v2.hf.space/sse",
            # Change from 'streamable_http' to 'sse'
            "transport": "sse",
        }
    }

    client = MultiServerMCPClient(mcp_server_config_hf)
    return await client.get_tools()


async def initialize_tools(tools_place: Literal['hosted_horizon', 'hosted_huggingface', 'local']) -> list:
    """Load local or hosted MCP tools according to given tool place and print a readable summary for debugging and return the list of tools."""
    if tools_place == 'hosted_horizon':
        tools = await get_hosted_horizon_mcp_tools()
    elif tools_place == 'hosted_huggingface':
        tools = await get_hosted_huggingface_mcp_tools()
    else:
        tools = await get_local_mcp_tools()

    return tools

# if __name__ == "__main__":
#     tools = asyncio.run(initialize_tools('hosted'))
#     print(f"Discovered {len(tools)} tools:")
#     for tool in tools:
#         print(f" - {tool.name}")