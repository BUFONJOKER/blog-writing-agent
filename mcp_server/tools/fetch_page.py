from pathlib import Path
import re
import sys

from tavily import TavilyClient
import tiktoken

# Support running this file directly from tools/ as a script.
if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import Config



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

def fetch_page_tool(url: str, query: str = "") -> dict:
    """
    Fetch a webpage using Tavily, clean it, and return safe LLM-ready content.
    Use this tool when:
    - You need to retrieve and process content from a specific URL.
    - You want to extract the main text and title from a webpage while removing junk.
    - You want to ensure the content is within token limits for LLM processing.
    Inputs:
    - url (str): The URL of the webpage to fetch.
    Outputs:
    - dict: A dictionary containing 'title', 'content', and 'source' (URL).
    """

    # 1. Validate input
    if not url.startswith("http"):
        return {
            "error": "Invalid URL format",
            "message": "URL must start with http/https"
        }

    try:
        response = tavily.extract(
        urls=url,
        query=query if query else None,
        extract_depth="advanced"
    )
    except Exception as exc:
        return {
            "error": "Tavily extraction failed",
            "message": str(exc)
        }

    if not response["results"]:
        return {"error": "No content found"}

    raw_content = response["results"][0]["raw_content"]

    title, cleaned_text = clean_content(raw_content)

    safe_text = truncate_tokens(cleaned_text, max_tokens=1000)

    return {
        "title": title,
        "content": safe_text,
        "source": url
    }
