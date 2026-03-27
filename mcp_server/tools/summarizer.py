from pydantic import Field

def summarize_research(content: str = Field(..., description="The raw, unprocessed text string scraped from the web."), topic: str = Field(..., description="The specific technical subject to isolate from the surrounding noise (e.g., 'Python 3.13 JIT Compiler')."), max_words: int = Field(1000, ge=100, le=1500, description="Target word count for the detailed brief. Range: 100 to 1500. Default: 1000.")) -> str:
    """
    Orchestrates an exhaustive technical synthesis of raw research data into a high-density brief.

    WHEN TO USE:
    - Use during the 'Synthesis Phase' after retrieving raw text via fetch_page_tool.
    - Use when the source material is fragmented, 'noisy' (ads/menus), or exceeds 2,000 characters.
    - Use to isolate critical technical evidence like version numbers (e.g., Python 3.13), performance metrics, and architectural changes.
    WHEN NOT TO USE:
    - Do not use if the content is already a concise summary or under 500 characters.
    - Do not use for initial web discovery (use web_search_tool instead).

    INPUTS:
    - content (str): The raw, unprocessed text string scraped from the web.
    - topic (str): The specific technical subject to isolate from the surrounding noise (e.g., 'Python 3.13 JIT Compiler').
    - max_words (int): Target word count for the detailed brief. Range: 100 to 1500. Default: 1000.

    OUTPUT:
    - Returns a structured 'Summarization Directive'.
    - IMPORTANT: Upon receiving this output, you MUST act as a Technical Editor and generate the 1000-word summary immediately before proceeding to planning.
    - Your internal analysis must prioritize: Hard Data, Core Arguments, and Developer Impact.
    """
    if not content or len(content.strip()) < 500:
        return "ERROR: Insufficient content for a 1000-word deep-dive."

    # The Instruction Block: Designed to force depth and length
    instructions = (
        f"### DEEP-DIVE RESEARCH DIRECTIVE ###\n"
        f"TOPIC: {topic}\n"
        f"TARGET LENGTH: {max_words} words\n\n"
        f"INSTRUCTION: Act as a Senior Technical Lead. Generate an exhaustive, "
        f"1000-word technical summary of the research provided below. \n\n"
        f"STRUCTURE YOUR RESPONSE INTO THESE SECTIONS:\n"
        f"1. **Executive Summary**: A high-level technical overview of '{topic}'.\n"
        f"2. **Detailed Technical Breakdown**: Explore features, version numbers (e.g., Python 3.13), "
        f"and architectural changes in depth.\n"
        f"3. **Performance & Benchmarks**: List any specific stats, dates, or metrics found.\n"
        f"4. **Developer Impact**: Detailed analysis of how this affects existing workflows.\n"
        f"5. **Comparative Analysis**: How this compares to previous versions or competitors.\n\n"
        f"STRICT RULES:\n"
        f"- **No Fluff**: Do not use repetitive 'filler' text to hit the word count. Use technical depth.\n"
        f"- **Ignore Noise**: Strip out all menu items, 'infoq' footers, and login prompts.\n"
        f"- **Format**: Use Markdown headers (##) and detailed paragraphs.\n\n"
        f"--- RAW RESEARCH START ---\n"
        f"{content[:25000]}\n"  # Increased window to provide enough data for 1000 words
        f"--- RAW RESEARCH END ---"
    )

    return instructions