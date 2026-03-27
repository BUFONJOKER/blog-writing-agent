import re
from collections import Counter
from typing import List

def extract_keywords_tool(text: str, topic: str, max_keywords: int = 10) -> str:
    """
    Expert SEO Keyword Extractor for the 'Optimization Phase' of blog planning.

    WHEN TO USE:
    - Use when you have completed raw research and summarization and need to identify impactful SEO terms.
    - Use as the final bridge when moving from the 'Research Phase' to the 'Planning Phase'.
    - Use to ensure the post targets a specific technical audience (e.g., Data Scientists using WSL2).
    WHEN NOT TO USE:
    - Do not use before you have a technical summary or raw research text.
    - Do not use for general brainstorming without source material.

    INPUTS:
    - text (str): The research summary or technical brief to be analyzed.
    - topic (str): The primary subject (e.g., 'Python 3.13 Internals') to ensure relevance.
    - max_keywords (int): Number of keywords to identify. Range: 5 to 15. Default: 10.

    OUTPUT & AGENT RESPONSIBILITY:
    - This tool returns a 'Structured Extraction Directive' containing a high-confidence baseline of terms.
    - IMPORTANT: This tool DOES NOT return the final keywords. It returns an instruction set.
    - You MUST perform an internal analysis of the research text based on this directive.
    - Your final response MUST be ONLY a clean JSON array of strings (e.g., ["keyword1", "keyword2"]).
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
