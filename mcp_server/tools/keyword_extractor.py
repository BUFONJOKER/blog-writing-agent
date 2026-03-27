import re
from collections import Counter
from typing import List

def extract_keywords_tool(text: str, topic: str, max_keywords: int = 10) -> str:
    """
    Expert SEO Keyword Extractor for Blog Planning.

    Use this tool when:
    - You have completed raw research and need to identify the most impactful SEO terms before creating a blog outline.
    - You need to ensure the final post is discoverable and targets the correct technical audience.
    - You are moving from the 'Research Phase' to the 'Planning Phase' in your workflow.

    What this tool does:
    1. Perfroms a frequency analysis of technical terms in the provided research.
    2. Generates a targeted instruction for you (the Agent) to refine these terms based on the specific 'topic'.
    3. Requires you to output a final list as a clean JSON array of strings to maintain data structure for the Planner.

    Returns:
    A structured extraction directive providing a high-confidence baseline of technical terms.

    This tool does not return the final keywords directly; instead, it outputs an instruction
    set that requires you (the Agent) to perform an internal analysis of the research text.

    Your response to this tool's output MUST be a standalone, clean JSON array of 5–10
    (or `max_keywords`) strings.

    Example Output Format: ["python 3.13", "software architecture", "performance"].
    """
    # 1. Validation & Cleaning
    if not text or len(text.strip()) < 50:
        return "Error: Input text is too short for meaningful SEO analysis."

    # 2. Logic-Based Fallback (No-API)
    # This runs locally to provide a 'baseline' if the LLM struggles
    def get_baseline(content: str) -> List[str]:
        junk = {"https", "http", "action", "infoq", "register", "login", "view"}
        words = re.findall(r'\b\w{4,}\b', content.lower())
        filtered = [w for w in words if w not in junk and not w.isdigit()]
        return [word for word, count in Counter(filtered).most_common(max_keywords)]

    baseline = get_baseline(text)

    # 3. THE LLM INSTRUCTION (The "LLM Call")
    # Instead of calling an API, we return this string to the Agent.
    # The Agent receives this and performs the extraction.
    instruction = (
        f"### SEO EXTRACTION TASK ###\n"
        f"TOPIC: {topic}\n"
        f"MAX KEYWORDS: {max_keywords}\n\n"
        f"INSTRUCTION: Analyze the research text provided below. Identify the most "
        f"valuable SEO keywords that will help this blog post rank for '{topic}'.\n"
        f"BASELINE SUGGESTIONS: {', '.join(baseline)}\n\n"
        f"FORMAT: Return ONLY a valid JSON array of strings (e.g., ['word1', 'word2']).\n\n"
        f"RESEARCH TEXT (Truncated for context):\n{text[:8000]}"
    )

    return instruction
