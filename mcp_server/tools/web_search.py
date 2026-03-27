from pathlib import Path
import sys

from tavily import TavilyClient

# Support running this file directly from tools/ as a script.
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import Config

def web_search_tool(query: str) -> dict:
    """"
    Search the internet for real-time information, news, and technical documentation.

    Use this tool when:
    - The user asks about current events or news after your knowledge cutoff.
    - You need to verify specific facts, statistics, or technical details.
    - You need to gather background research for blog posts or articles.
    - The user asks for information you don't have in your local training data.

    Args:
        query (str): A clear, descriptive search query (e.g., 'latest features of Python 3.13'
                     or 'current trends in AI writing 2026').

    Returns:
        list: A list of objects containing 'title', 'url', 'content' (snippet), and 'score'.
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
