from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio

async def get_mcp_tools():
    """
    Create an MCP client and fetch all tools exposed by the MCP server.

    Returns:
    list: Tool objects discovered from the configured MCP server.
    """
    # Define the MCP server configuration with the appropriate command and arguments to start the server
    mcp_server_config = {
        "blog-research-tools": {
            "transport": "stdio",
            "command": "uv",
            "args": [
                "run",
                "--project",
                "/home/mani/data-science/llm-projects/blog-writing-agent/mcp_server",
                "python",
                "/home/mani/data-science/llm-projects/blog-writing-agent/mcp_server/server.py",
            ],
        }
    }
    # Initialize the MCP client with the server configuration and fetch the tools
    client = MultiServerMCPClient(mcp_server_config)
    tools = await client.get_tools()

    return tools


async def initialize_tools():
    """
    Initialize tool loading for startup and print discovered tools.
    """
    tools = await get_mcp_tools()
    print("Available tools:", tools)

if __name__ == "__main__":
    asyncio.run(initialize_tools())