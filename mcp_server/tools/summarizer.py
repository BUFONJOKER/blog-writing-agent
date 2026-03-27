def summarize_research(content: str, topic: str, max_words: int = 1000) -> str:
    """
    Orchestrates an exhaustive, 1000-word technical synthesis of research data.

    Use this tool when:
    - You have successfully fetched raw text (via fetch_page_tool) and need a high-density foundation for a long-form blog post.
    - The raw content is too fragmented or 'noisy' (containing ads/menus) to be used directly in a draft.
    - You need to extract specific technical evidence, such as version numbers (e.g., Python 3.13), performance metrics, or architectural changes.

    How to handle the output:
    - This tool returns a structured 'Summarization Directive'.
    - Upon receiving the output, you MUST act as a Technical Editor and generate the 1000-word summary immediately before proceeding to the next planning step.
    - Focus your internal analysis on: Hard Data, Core Arguments, and Developer Impact.

    Args:
        content (str): The raw, unprocessed text string scraped from the web.
        topic (str): The specific subject matter to isolate from the noise (e.g., 'Python 3.13 JIT Compiler').
        max_words (int): The target length of the detailed technical brief. Defaults to 1000.
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