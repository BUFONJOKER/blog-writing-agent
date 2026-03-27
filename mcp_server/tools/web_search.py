from pathlib import Path
import sys

from tavily import TavilyClient

# Support running this file directly from tools/ as a script.
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import Config

def web_search_tool(query: str) -> dict:
    """
    Performs a real-time internet search to retrieve technical documentation, news, and factual data.

    WHEN TO USE:
    - Use as the initial 'Discovery Phase' to find authoritative source URLs for a blog topic.
    - Use to verify specific version numbers (e.g., 'Python 3.13 features'), benchmarks, or release dates.
    - Use when the required information is likely updated after your internal knowledge cutoff (2026 context).

    WHEN NOT TO USE:
    - Do not use if the user provides a specific URL (use fetch_page_tool instead).
    - Do not use for general logic, coding assistance, or internal data science concepts already in your training data.

    INPUTS:
    - query (str): A precise, technical search string.
      Example: 'Python 3.13 JIT compiler performance vs 3.12' or 'FastAPI best practices 2026'.
    - max_results (int): The number of search results to return.
      Range: 1 to 10. Default: 5.

    OUTPUT:
    - Returns a list of result objects. Each object contains:
        * 'title': The headline of the webpage.
        * 'url': The absolute link (needed for fetch_page_tool).
        * 'content': A short text snippet for initial relevance filtering.
        * 'score': A relevancy ranking from 0.0 to 1.0.
    """

    if not query or not query.strip():
        raise ValueError("Query must be a non-empty string")

    if not Config.TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY is not configured")

    try:
        tavily_client = TavilyClient(api_key=Config.TAVILY_API_KEY)
        response = tavily_client.search(query)
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
