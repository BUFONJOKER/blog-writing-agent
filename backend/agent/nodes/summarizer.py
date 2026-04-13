from agent.state import BlogAgentState
import asyncio
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate


FALLBACK_SUMMARY = "No useful research data could be generated."


def _normalize_content(content: object) -> str:
    """Normalize arbitrary message content into a plain string.

    Args:
        content: Raw content that may be a string, list, dict-like object, or scalar.

    Returns:
        str: A normalized string representation of the input content.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        if not content:
            return ""
        first = content[0]
        if isinstance(first, dict):
            return str(first.get("text", ""))
        return str(first)
    return str(content or "")


def _snippet_from_result(result: dict, max_chars: int = 300) -> str:
    """Build a short snippet from a single research result.

    Args:
        result: Research result dictionary containing content to summarize.
        max_chars: Maximum number of characters to include in the snippet.

    Returns:
        str: A short human-readable excerpt or a fallback marker.
    """
    content = " ".join((result.get("content") or "").split())
    if not content:
        return "No content"
    if len(content) <= max_chars:
        return content
    return content[:max_chars] + "..."


def _build_fallback_research_summary(results: list[dict]) -> str:
    """Construct a readable summary from raw research result records.

    Args:
        results: Collection of research result dictionaries.

    Returns:
        str: A markdown-like summary of the available research results.
    """
    if not results:
        return FALLBACK_SUMMARY

    lines = []
    for i, result in enumerate(results, start=1):
        title = (result.get("title") or "Untitled source").strip()
        url = str(result.get("url") or "").strip()
        insight = _snippet_from_result(result)
        lines.append(f"{i}. {title}\n   URL: {url}\n   Insight: {insight}")

    return "Detailed Extracted Data:\n" + "\n".join(lines)


def _ensure_non_empty_summary(summary: object, fallback: object = "") -> str:
    """Return the first non-empty summary candidate.

    Args:
        summary: Primary summary content to validate.
        fallback: Secondary summary content used when the primary is empty.

    Returns:
        str: A non-empty summary string or a standard fallback message.
    """
    summary_text = _normalize_content(summary).strip()
    if summary_text:
        return summary_text

    fallback_text = _normalize_content(fallback).strip()
    if fallback_text:
        return fallback_text

    return FALLBACK_SUMMARY


async def summarizer_node(state: BlogAgentState, model) -> dict:
    """Condense research or model knowledge into a blog-ready summary.

    Args:
        state: Current workflow state containing the prompt and research data.
        model: Language model used to generate the summary.

    Returns:
        dict: Updated research summary and message history entries.
    """
    # model = load_model()
    fallback_from_results = _build_fallback_research_summary(state.research_results)
    # 1. Determine the source of data
    if state.needs_research:
        # Use research gathered from the web
        source_data = _ensure_non_empty_summary(
            state.research_summary,
            fallback_from_results,
        )
    else:
        # Use internal model knowledge for general topics
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    (
                        "You are a Senior Technical Lead. Your task is to provide a concise, "
                        "high-quality summary of the following topic based on your internal knowledge. "
                        "Focus on key insights and technical accuracy. "
                        "Your response must never be empty."
                    ),
                ),
                (
                    "human",
                    "Topic: {topic}\n\nProvide a summary based on your knowledge.",
                ),
            ]
        )

        chain = prompt | model
        response = await chain.ainvoke({"topic": state.topic})
        source_data = _ensure_non_empty_summary(response.content, FALLBACK_SUMMARY)
    # 2. Define the Summarization Prompt
    # We combine the system role and the data in one template
    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                (
                    "You are a Senior Technical Lead. Your task is to provide a concise, "
                    "high-quality summary of the following data for a blog post. "
                    "Focus on key insights and technical accuracy. "
                    "FINAL OUTPUT REQUIREMENTS: always provide a summary, never return empty output, "
                    "and explicitly say when evidence is limited."
                ),
            ),
            ("human", "Topic: {topic}\n\nData to summarize: {data}"),
        ]
    )

    # 3. Generate Summary directly via LLM
    chain = prompt_template | model

    input_variables = {"topic": state.topic, "data": source_data}

    final_response = await chain.ainvoke(input_variables)
    final_summary = _ensure_non_empty_summary(
        final_response.content,
        source_data,
    )

    # 4. Prepare messages for state tracking
    # We store the final summary as an AIMessage
    ai_msg = AIMessage(content=final_summary)

    return {"research_summary": final_summary, "messages": [ai_msg]}
