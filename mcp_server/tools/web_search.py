from pathlib import Path
import sys

from tavily import TavilyClient

# Support running this file directly from tools/ as a script.
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import Config
from pydantic import Field

def web_search_tool(
    query: str = Field(..., description="A precise, technical search string."),
    max_results: int = Field(5, description="Number of results to return (1-10).") # Add this
) -> dict:
    """
    Performs a real-time internet search...
    """

    if not query or not query.strip():
        raise ValueError("Query must be a non-empty string")

    # Ensure max_results is an integer even if the LLM sends a string
    try:
        max_results = int(max_results)
    except (ValueError, TypeError):
        max_results = 5

    try:
        tavily_client = TavilyClient(api_key=Config.TAVILY_API_KEY)
        # Pass max_results to the tavily client
        response = tavily_client.search(query, max_results=max_results)
    except Exception as exc:
        raise RuntimeError(f"Tavily search request failed: {exc}") from exc

    results = response.get("results") if isinstance(response, dict) else None
    if not results:
        raise LookupError("No search results returned from Tavily")

    result = results[0]
    missing_fields = [key for key in ("url", "title", "content", "score") if key not in result]
    if missing_fields:
        raise KeyError(f"Missing expected fields in Tavily result: {', '.join(missing_fields)}")

    web_search_results = {
        "url": result["url"],
        "title": result["title"],
        "content": result["content"],
        "score": result["score"],
    }

    return web_search_results
