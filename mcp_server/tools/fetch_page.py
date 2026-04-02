from pathlib import Path
import re
import sys
import unicodedata
from tavily import TavilyClient
import tiktoken
from pydantic import Field

# Support running this file directly
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import Config

# Initialize Tavily client
tavily = TavilyClient(api_key=Config.TAVILY_API_KEY)

# ---------------------------
# Helper: Clean content (Unicode-safe)
# ---------------------------
def clean_content(raw_content: str, metadata_title: str = None):
    if not raw_content:
        return "No Title Found", ""

    # Normalize newlines
    text = re.sub(r'\n{3,}', '\n\n', raw_content).strip()

    # Determine title
    title = "No Title Found"
    if metadata_title and len(metadata_title.strip()) > 5:
        title = metadata_title.strip()
    else:
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

    # Clean whitespace
    text = re.sub(r" +", " ", text)

    # Normalize Unicode
    text = unicodedata.normalize("NFKC", text)
    title = unicodedata.normalize("NFKC", title)

    # Ensure UTF-8 safety
    text = text.encode("utf-8", errors="replace").decode("utf-8")
    title = title.encode("utf-8", errors="replace").decode("utf-8")

    return title, text


# ---------------------------
# Helper: Token truncation
# ---------------------------
def truncate_tokens(text: str, max_tokens=1200):
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)

    if len(tokens) <= max_tokens:
        return text

    return enc.decode(tokens[:max_tokens]) + "\n\n[...Content Truncated...]"


# ---------------------------
# MAIN TOOL: Fetch Page
# ---------------------------
def fetch_page_tool(
    url: str = Field(..., description="The absolute URL to fetch."),
    query: str = Field("", description="The query to focus extraction on.")
) -> dict:
    """
    Retrieves and cleans full-text content from a specific URL for deep research.
    """

    # 1️⃣ Validate URL
    if not isinstance(url, str) or not url.startswith("http"):
        return {"error": f"Invalid URL: {url}", "source": url}

    try:
        # 2️⃣ Tavily extraction
        response = tavily.extract(
            urls=url,
            query=query if query else None,
            extract_depth="advanced"
        )
    except Exception as exc:
        return {"error": f"Tavily extraction failed: {str(exc)}", "source": url}

    results = response.get("results", [])
    if not results:
        return {"error": "No content extracted from URL.", "source": url}

    # 3️⃣ Merge top results (better coverage)
    merged_content = ""
    metadata_title = ""
    score = 0.0

    for res in results[:3]:  # take top 3 chunks
        merged_content += res.get("raw_content", "") + "\n\n"

        if not metadata_title and res.get("title"):
            metadata_title = res.get("title")

        score = max(score, res.get("score", 0.0))  # keep best score

    if not merged_content.strip():
        return {"error": "Extracted content is empty.", "source": url}

    # 4️⃣ Clean content
    title, cleaned_text = clean_content(merged_content, metadata_title)

    # 5️⃣ Truncate for LLM safety
    safe_text = truncate_tokens(cleaned_text, max_tokens=1200)

    # 6️⃣ Generate snippet (for lightweight context injection)
    snippet = " ".join(cleaned_text.split()[:60])  # first ~60 words

    # 7️⃣ Final structured output (JSON-safe)
    return {
        "tool": "fetch_page_tool",
        "title": title,
        "content": safe_text,
        "snippet": snippet,
        "source": url,
        "score": score,
        "word_count": len(cleaned_text.split())
    }
