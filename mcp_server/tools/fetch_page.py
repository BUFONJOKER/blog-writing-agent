from pathlib import Path
import re
import sys

from tavily import TavilyClient
import tiktoken

# Support running this file directly from tools/ as a script.
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import Config
from pydantic import Field


# Initialize client
tavily = TavilyClient(api_key=Config.TAVILY_API_KEY)

# ---------------------------
# Helper: Clean content
# ---------------------------
def clean_content(raw_content: str):
    text = raw_content.replace("\n", " ").strip()

    # Extract title
    lines = raw_content.split("\n")
    title = "No Title Found"
    for line in lines:
        line = line.strip()
        if len(line) > 20:
            title = line
            break

    # Remove junk
    junk_patterns = [
        r"Jump to content", r"Main menu", r"Search",
        r"Donate", r"Log in", r"Toggle the table of contents"
    ]

    for pattern in junk_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = re.sub(r"\s+", " ", text)

    return title, text

# ---------------------------
# Helper: Token truncation
# ---------------------------
def truncate_tokens(text: str, max_tokens=1000):
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    return enc.decode(tokens[:max_tokens])

def fetch_page_tool(url: str = Field(..., description="The absolute URL of the webpage to fetch (e.g., 'https://www.infoq.com/news/python-313-latest-features')"), query: str = Field("", description="The specific query to focus the extraction on, ensuring the resulting text is relevant to your blog goal.")) -> dict:
    """
    Core tool for the 'Extraction Phase'. Retrieves and cleans full-text content from a specific URL.

    WHEN TO USE:
    - Use AFTER obtaining a high-authority URL from the web_search_tool to get the full article text.
    - Use to extract the main technical content while automatically removing 'junk' like navigation menus, ads, and footers.
    - Use to ensure the content is formatted as safe, LLM-ready Markdown within token limits.

    WHEN NOT TO USE:
    - Do not use for initial broad research; use web_search_tool first to find relevant URLs.
    - Do not use if the search snippet from Tavily already contains all the factual data required.

    INPUTS:
    - url (str): The absolute URL of the webpage to fetch (e.g., 'https://www.infoq.com/news/python-313-latest-features').
    - query (str): The specific query to focus the extraction on, ensuring the resulting text is relevant to your blog goal.

    OUTPUT:
    - Returns a dictionary containing:
        * 'title': The cleaned page title.
        * 'content': The main article text in Markdown, truncated to approximately 1,000 tokens for efficient LLM processing.
        * 'source': The original URL for citation.
    """

    # 1. Validate input
    if not url.startswith("http"):
        raise ValueError("URL must start with http/https")

    try:
        response = tavily.extract(
        urls=url,
        query=query if query else None,
        extract_depth="advanced"
    )
    except Exception as exc:
        raise RuntimeError(f"Tavily extraction failed: {exc}") from exc

    if not response.get("results"):
        raise LookupError("No content found")

    raw_content = response["results"][0]["raw_content"]

    title, cleaned_text = clean_content(raw_content)

    safe_text = truncate_tokens(cleaned_text, max_tokens=1000)

    return {
        "title": title,
        "content": safe_text,
        "source": url
    }
