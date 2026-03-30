from agent.state import BlogAgentState
from agent.model import load_model
from langchain_core.prompts import ChatPromptTemplate


def _normalize_result(item: object) -> str:
    if isinstance(item, dict):
        tool_name = item.get("tool_name", "tool")
        content = item.get("content", "")
        return f"[{tool_name}] {content}"
    return str(item)


def summarizer_node(state: BlogAgentState) -> dict:
    """Summarize collected research outputs into a concise grounded context."""
    if not state.research_results:
        return {
            "research_summary": state.research_summary or "No external research results were collected.",
            "more_research_needed": False,
        }

    normalized = [_normalize_result(item) for item in state.research_results]
    source_text = "\n\n".join(normalized[:12])

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are a technical research summarizer. Produce a concise factual summary with key findings and any missing areas.",
        ),
        (
            "user",
            "User prompt:\n{prompt}\n\nResearch outputs:\n{research_outputs}\n\nReturn 5-8 bullet points in plain text.",
        ),
    ])

    try:
        model = load_model()
        chain = prompt | model
        response = chain.invoke({"prompt": state.prompt, "research_outputs": source_text})
        summary = getattr(response, "content", "") or "\n".join(normalized[:5])
    except Exception:
        summary = "\n".join(normalized[:5])

    return {
        "research_summary": summary,
        "more_research_needed": False,
    }