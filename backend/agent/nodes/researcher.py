import json
import re
from langchain_core.messages import ToolMessage, SystemMessage, HumanMessage
from agent.state import BlogAgentState
from agent.model import load_model


# 🔥 Futility keywords
FUTURE_KEYWORDS = [
    "has not happened",
    "hasn't happened",
    "is scheduled",
    "will be held",
    "upcoming",
    "yet to take place",
    "in the future",
    "not started",
    "no results available",
]

MAX_PARSED_RESULTS = 8
MAX_RESULTS_FOR_PROMPT = 5
MAX_CONTEXT_MESSAGES = 8


def is_futile_context(results):
    if not results:
        return False

    valid_results = [r for r in results if r.get("content", "").strip()]
    if not valid_results:
        return False

    matches = sum(
        1
        for r in valid_results
        if any(k in r.get("content", "").lower() for k in FUTURE_KEYWORDS)
    )

    # Consider context futile when at least half the usable evidence says data is not available yet.
    return (matches / len(valid_results)) >= 0.5


def _normalize_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        if not content:
            return ""
        first = content[0]
        if isinstance(first, dict):
            return first.get("text", "")
        return str(first)
    return str(content or "")


def _is_http_url(value: str) -> bool:
    return bool(value) and value.startswith(("http://", "https://"))


def _extract_results_from_tool_message(msg: ToolMessage) -> list[dict]:
    parsed: list[dict] = []
    content_str = _normalize_content(msg.content)

    try:
        data = json.loads(content_str)
    except (json.JSONDecodeError, TypeError, ValueError):
        data = None

    if isinstance(data, dict):
        if isinstance(data.get("results"), list):
            for r in data["results"]:
                if not isinstance(r, dict):
                    continue
                url = (r.get("url") or "").strip()
                if not _is_http_url(url):
                    continue
                parsed.append(
                    {
                        "tool": getattr(msg, "name", "web_search"),
                        "title": r.get("title", ""),
                        "content": r.get("content", ""),
                        "url": url,
                        "score": r.get("score", 0.0),
                    }
                )
        else:
            url = (data.get("url") or data.get("source") or "").strip()
            if _is_http_url(url):
                parsed.append(
                    {
                        "tool": getattr(msg, "name", "web_search"),
                        "title": data.get("title", ""),
                        "content": data.get("content", ""),
                        "url": url,
                        "score": data.get("score", 0.0),
                    }
                )

    if not parsed:
        url_match = re.search(r"https?://\S+", content_str)
        if url_match:
            parsed.append(
                {
                    "tool": getattr(msg, "name", "web_search"),
                    "title": "",
                    "content": content_str,
                    "url": url_match.group(0),
                    "score": 0.0,
                }
            )

    return parsed


def _merge_unique_results(existing: list[dict], new_items: list[dict]) -> list[dict]:
    merged: list[dict] = []
    seen_urls = set()

    for item in [*(existing or []), *(new_items or [])]:
        url = (item.get("url") or "").strip()
        if not _is_http_url(url) or url in seen_urls:
            continue
        seen_urls.add(url)
        merged.append(item)

    return merged


def _build_research_summary(synthesis: str, results: list[dict]) -> str:
    sections: list[str] = []
    synthesis_text = (synthesis or "").strip()

    if synthesis_text:
        sections.append(synthesis_text)

    if results:
        datapoints = []
        for i, result in enumerate(results, start=1):
            title = (result.get("title") or "Untitled source").strip()
            url = (result.get("url") or "").strip()
            content = " ".join((result.get("content") or "").split())
            snippet = content[:280] + ("..." if len(content) > 280 else "")

            datapoints.append(f"{i}. {title}\n   URL: {url}\n   Data point: {snippet}")

        sections.append("Retrieved data points:\n" + "\n".join(datapoints))

    return "\n\n".join(sections).strip()


def _build_terminal_summary(message: str, results: list[dict]) -> str:
    return _build_research_summary(message, results)


def _extract_results_from_tool_messages(messages: list[ToolMessage]) -> list[dict]:
    results: list[dict] = []
    for msg in messages:
        results.extend(_extract_results_from_tool_message(msg))
    return results


def _unique_by_url(results: list[dict]) -> list[dict]:
    unique_results: list[dict] = []
    seen_urls = set()

    for result in results:
        url = (result.get("url") or "").strip()
        if not _is_http_url(url) or url in seen_urls:
            continue
        seen_urls.add(url)
        unique_results.append(result)

    return unique_results


async def researcher_node(state: BlogAgentState, tools: list) -> dict:
    """
    Executes the 'Retrieval Phase' with logic to encourage deep extraction via fetch_page_tool.
    This node loops until the LLM decides it has enough detailed information.
    """
    model = load_model()
    # Bind the provided tools (web_search_tool and fetch_page_tool) to the model
    model_with_tools = model.bind_tools(tools)

    # Rebuild the full accumulated memory from every tool message seen in the session.
    all_tool_messages = [msg for msg in state.messages if isinstance(msg, ToolMessage)]
    historical_results = _unique_by_url(
        _extract_results_from_tool_messages(all_tool_messages)
    )

    combined_results = _merge_unique_results(state.research_results, historical_results)
    parsed_new_results = [
        result
        for result in historical_results
        if (result.get("url") or "").strip()
        and (result.get("url") or "").strip()
        not in {
            ((existing.get("url") or "").strip()) for existing in state.research_results
        }
    ][:MAX_PARSED_RESULTS]
    prompt_results = sorted(
        combined_results, key=lambda x: x.get("score", 0.0), reverse=True
    )[:MAX_RESULTS_FOR_PROMPT]
    visited_urls = [
        r.get("url", "")
        for r in combined_results
        if _is_http_url((r.get("url") or "").strip())
    ]

    search_history_context = ""
    for i, res in enumerate(prompt_results, start=1):
        snippet = " ".join((res.get("content") or "").split()[:50])
        search_history_context += f"""
            --- Source [{i}] ---
            Title: {res.get('title', '')}
            URL: {res.get('url', '')}
            Content: {snippet}
            Score: {res.get('score', 0.0)}
            """

    if not combined_results and (state.tool_call_count or 0) > 0:
        return {
            "messages": [],
            "research_results": [],
            "research_summary": _build_terminal_summary(
                "No useful data could be retrieved.",
                combined_results,
            ),
            "has_tool_calls": False,
            "more_research_needed": False,
        }

    if is_futile_context(prompt_results):
        return {
            "messages": [],
            "research_results": parsed_new_results,
            "research_summary": _build_terminal_summary(
                (
                    "The requested information does not exist yet. "
                    "This topic refers to a future or incomplete event, "
                    "so no factual data is available."
                ),
                combined_results,
            ),
            "has_tool_calls": False,
            "more_research_needed": False,
        }

    # ---------------------------
    # 🚨 4️⃣ TOOL CALL LIMIT GUARD
    # ---------------------------
    MAX_TOOL_CALLS = state.max_tool_calls or 8
    if state.tool_call_count and state.tool_call_count >= MAX_TOOL_CALLS:
        return {
            "messages": [],
            "research_results": parsed_new_results,
            "research_summary": _build_terminal_summary(
                (
                    "Research stopped due to insufficient or unavailable data. "
                    "Further tool calls are unlikely to provide new insights."
                ),
                combined_results,
            ),
            "has_tool_calls": False,
            "more_research_needed": False,
        }

    # ---------------------------
    # 6️⃣ Improved system prompt (adds STOP condition)
    # ---------------------------
    system_prompt = (
        "You are a Senior Research Assistant.\n\n"
        "STRATEGY:\n"
        "1. Use 'web_search_tool' for discovery.\n"
        "2. Use 'fetch_page_tool' only when deeper content is needed.\n\n"
        "STOP CONDITION:\n"
        "If the information does not exist (future events, unknown results), "
        "STOP and provide a final answer. DO NOT call tools again.\n\n"
        "RE-USE POLICY:\n"
        "Do not fetch URLs that are already visited unless you need a different section not captured yet.\n\n"
        "AVOID:\n"
        "- Repeating the same search query "
        "- Fetching the same URL multiple times\n\n"
        "RULES:\n"
        "- web_search_tool → only 'query'\n"
        "- fetch_page_tool → 'url' + 'query'"
    )

    # 3. Construct the Human Message with injected URL context
    query_text = ", ".join(state.research_queries)
    user_content = f"Research these topics deeply: {query_text}"

    # If we have previous results, we tell the model to use them as a target for fetching
    if search_history_context:
        user_content += (
            f"\n\nReview your previous findings below. If any URL looks highly relevant but the "
            f"snippet is too short, use 'fetch_page_tool' on that URL now:\n{search_history_context}"
        )
    if visited_urls:
        user_content += (
            "\n\nAlready visited URLs (avoid re-fetching unless there is a clear new reason):\n"
            + "\n".join(f"- {url}" for url in visited_urls[:20])
        )

    recent_messages = state.messages[-MAX_CONTEXT_MESSAGES:]
    clean_messages = [
        SystemMessage(content=system_prompt),
        *recent_messages,
        HumanMessage(content=user_content),
    ]

    # 4. Invoke model
    response = await model_with_tools.ainvoke(clean_messages)

    # 5. Determine state updates for the LangGraph loop
    has_tool_calls = bool(response.tool_calls)

    current_calls = len(response.tool_calls) if response.tool_calls else 0

    update = {
        "messages": [response],
        "research_results": parsed_new_results,
        "has_tool_calls": has_tool_calls,
        # BlogAgentState uses operator.add for tool_call_count; return only the delta for this step.
        "tool_call_count": current_calls,
    }

    # Signal if we need to stay in the research loop or proceed to writing
    if not response.tool_calls:
        update["research_summary"] = _build_terminal_summary(
            response.content,
            combined_results,
        )
        update["more_research_needed"] = False
    else:
        update["more_research_needed"] = True

    return update
