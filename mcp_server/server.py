from fastmcp import FastMCP
from tools.web_search import web_search_tool
from tools.fetch_page import fetch_page_tool
from tools.keyword_extractor import extract_keywords_tool

mcp = FastMCP("blog-researrch-tools")

mcp.tool()(web_search_tool)

mcp.tool()(fetch_page_tool)

mcp.tool()(extract_keywords_tool)
if __name__ == "__main__":
    mcp.run()