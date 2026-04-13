import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from agent.config import HORIZON_TOKEN
from typing import Literal


async def get_local_mcp_tools() -> list:
    """Fetch tool definitions from the local MCP server over stdio.

    Args:
        None: The MCP server configuration is built internally.

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

    Args:
        None: The hosted MCP configuration is built internally.

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

    client = MultiServerMCPClient(mcp_server_config)
    return await client.get_tools()


async def get_hosted_huggingface_mcp_tools() -> list:
    """Fetch tool definitions from the hosted MCP server on Hugging Face Spaces.

    Args:
        None: The Hugging Face MCP configuration is built internally.

    Returns:
        list: Tool objects discovered from the hosted MCP server.
    """

    mcp_server_config_hf = {
        "blog-research-tools-hf": {
            # Use the /sse suffix shown in your logs
            "url": "https://bufon-joker-blog-writing-agent-mcp-server-v2.hf.space/sse",
            # "url": "http://localhost:8000/sse",
            # # Change from 'streamable_http' to 'sse'
            "transport": "sse",
        }
    }

    client = MultiServerMCPClient(mcp_server_config_hf)
    return await client.get_tools()


async def initialize_tools(
    tools_place: Literal["hosted_horizon", "hosted_huggingface", "local"],
) -> list:
    """Load MCP tools from the requested environment.

    Args:
        tools_place: Tool source selector for local or hosted deployments.

    Returns:
        list: Tool objects discovered from the selected MCP server.
    """
    if tools_place == "hosted_horizon":
        tools = await get_hosted_horizon_mcp_tools()
    elif tools_place == "hosted_huggingface":
        tools = await get_hosted_huggingface_mcp_tools()
    else:
        tools = await get_local_mcp_tools()

    return tools


if __name__ == "__main__":
    tools = asyncio.run(initialize_tools("hosted_huggingface"))
    print(f"Discovered {len(tools)} tools:")
    for tool in tools:
        print(f" - {tool.name}")
