from pathlib import Path
import re
import sys
from tavily import TavilyClient
import tiktoken
from pydantic import Field

# Support running this file directly
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import Config

# Initialize client
tavily = TavilyClient(api_key=Config.TAVILY_API_KEY)

# ---------------------------
# Helper: Clean content
# ---------------------------
def clean_content(raw_content: str, metadata_title: str = None):
    # Remove excessive newlines but keep some structure
    text = re.sub(r'\n{3,}', '\n\n', raw_content).strip()

    # Determine Title: Use Tavily's metadata title first
    title = "No Title Found"
    if metadata_title and len(metadata_title.strip()) > 5:
        title = metadata_title.strip()
    else:
        # Fallback: Look for the first substantial line
        lines = [line.strip() for line in raw_content.split("\n") if len(line.strip()) > 20]
        if lines:
            title = lines[0]

    # Remove junk/UI elements
    junk_patterns = [
        r"Jump to content", r"Main menu", r"Search",
        r"Donate", r"Log in", r"Toggle the table of contents",
        r"Cookie Policy", r"Privacy Policy", r"Terms of Service"
    ]

    for pattern in junk_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Clean up whitespace
    text = re.sub(r" +", " ", text)

    return title, text

# ---------------------------
# Helper: Token truncation
# ---------------------------
def truncate_tokens(text: str, max_tokens=1200): # Increased slightly for better context
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return enc.decode(tokens[:max_tokens]) + "\n\n[...Content Truncated due to Limit...]"

def fetch_page_tool(
    url: str = Field(..., description="The absolute URL to fetch."),
    query: str = Field("", description="The query to focus extraction on.")
) -> dict:
    """
    Retrieves and cleans full-text content from a specific URL for deep research.
    """

    if not url.startswith("http"):
        raise ValueError(f"Invalid URL: {url}. Must start with http/https")

    try:
        # Use advanced depth for better quality technical content
        response = tavily.extract(
            urls=url,
            query=query if query else None,
            extract_depth="advanced"
        )
    except Exception as exc:
        return {"error": f"Tavily extraction failed: {str(exc)}", "source": url}

    if not response.get("results") or len(response["results"]) == 0:
        return {"error": "No content could be extracted from this URL.", "source": url}

    result_data = response["results"][0]
    raw_content = result_data.get("raw_content", "")
    metadata_title = result_data.get("title", "")

    if not raw_content:
        return {"error": "URL returned empty content.", "source": url}

    # Clean and Format
    title, cleaned_text = clean_content(raw_content, metadata_title)
    safe_text = truncate_tokens(cleaned_text, max_tokens=1200)

    return {
        "title": title,
        "content": safe_text,
        "source": url,
        "word_count": len(cleaned_text.split())
    }