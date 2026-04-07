from pathlib import Path
import sys

from tavily import TavilyClient
import json
# Support running this file directly from tools/ as a script.
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import TAVILY_API_KEY
from pydantic import Field

def web_search_tool(
    query: str = Field(..., description="A precise, technical search string."),
    max_results: int = Field(5, description="Number of results to return (1-10).") # Add this
):
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

    max_results = max(1, min(max_results, 10))  # clamp 1–10

    try:
        tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
        # Pass max_results to the tavily client
        response = tavily_client.search(query, max_results=max_results)
    except Exception as exc:
        raise RuntimeError(f"Tavily search request failed: {exc}") from exc

    results = response.get("results", [])
    if not results:
        return json.dumps({"results": []})

    # ✅ Process ALL results
    processed_results = []
    for r in results:
        processed_results.append({
            "url": r.get("url", ""),
            "title": r.get("title", ""),
            "content": r.get("content", ""),
            "score": r.get("score", 0.0)
        })

    # ✅ Return JSON string (important for ToolMessage parsing)
    return json.dumps({
        "query": query,
        "results": processed_results
    })
