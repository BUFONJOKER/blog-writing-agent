from fastmcp import FastMCP
from tools.web_search import web_search_tool
from tools.fetch_page import fetch_page_tool


mcp = FastMCP("blog-research-tools")

# Register tools
mcp.tool()(web_search_tool)
mcp.tool()(fetch_page_tool)

if __name__ == "__main__":
    import sys
    import os

    # Check if we specifically asked for a web server (deployment mode)
    if "--sse" in sys.argv:
        # Port 8000 is standard for Docker/Cloud deployments
        port = int(os.getenv("PORT", 8000))
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        # Default to stdio for local Cursor/CLI use
        mcp.run()