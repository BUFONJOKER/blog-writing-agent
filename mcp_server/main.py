import re
from collections import Counter
from typing import List
from fastmcp import FastMCP

# Initialize FastMCP
mcp = FastMCP("KeywordExtractor")

@mcp.tool()
def extract_keywords_tool(text: str, topic: str, max_keywords: int = 10) -> str:
    """
    Extracts a JSON array of the top SEO-relevant keywords from the research content.
    """
    if not text or len(text.strip()) < 50:
        return "Error: Input text is too short."

    # Logic-Based Fallback (No-API)
    def get_baseline(content: str) -> List[str]:
        junk = {"https", "http", "action", "infoq", "register", "login", "view"}
        words = re.findall(r'\b\w{4,}\b', content.lower())
        filtered = [w for w in words if w not in junk and not w.isdigit()]
        return [word for word, count in Counter(filtered).most_common(max_keywords)]

    baseline = get_baseline(text)

    # Return the instruction for the LLM
    return (
        f"### SEO EXTRACTION TASK ###\n"
        f"TOPIC: {topic}\n"
        f"BASELINE: {', '.join(baseline)}\n\n"
        f"INSTRUCTION: Extract {max_keywords} SEO keywords from the text below.\n"
        f"FORMAT: Return ONLY a JSON array of strings.\n\n"
        f"TEXT:\n{text[:5000]}"
    )

if __name__ == "__main__":
    mcp.run()