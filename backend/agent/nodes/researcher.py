
import json
import re
from langchain_core.messages import ToolMessage, SystemMessage, HumanMessage
from agent.state import BlogAgentState
from agent.model import load_model


# 🔥 Futility keywords
FUTURE_KEYWORDS = [
    "has not happened", "hasn't happened", "is scheduled",
    "will be held", "upcoming", "yet to take place",
    "in the future", "not started", "no results available"
]

def is_futile_context(results):
    matches = 0
    valid = 0

    for r in results:
        content = r.get("content", "")
        if not content.strip():
            continue

        valid += 1
        if any(k in content.lower() for k in FUTURE_KEYWORDS):
            matches += 1

    if valid == 0:
        return False

    return matches >= max(2, valid // 2)

async def researcher_node(state: BlogAgentState, tools: list) -> dict:
    """
    Executes the 'Retrieval Phase' with logic to encourage deep extraction via fetch_page_tool.
    This node loops until the LLM decides it has enough detailed information.
    """
    model = load_model()
    # Bind the provided tools (web_search_tool and fetch_page_tool) to the model
    model_with_tools = model.bind_tools(tools)

    # 1. Context Injection: Extract previous tool results to provide a "memory" of URLs
    search_history_context = ""
    new_results = []
    seen_urls = set()

    for msg in reversed(state.messages):
        if isinstance(msg, ToolMessage):

            content_str = msg.content
            if isinstance(content_str, list):
                content_str = content_str[0].get("text", "") if content_str else ""

            try:
                data = json.loads(content_str)

                # ✅ MULTI-RESULT SUPPORT
                if "results" in data:
                    for r in data["results"]:

                        if len(new_results) >= 8:
                            break

                        url = r.get("url") or ""
                        if not url:
                            continue

                        if url in seen_urls:
                            continue
                        seen_urls.add(url)

                        new_results.append({
                            "tool": getattr(msg, "name", "web_search"),
                            "title": r.get("title", ""),
                            "content": r.get("content", ""),
                            "url": url,
                            "score": r.get("score", 0.0)
                        })

                else:
                    url = data.get("url") or data.get("source", "N/A")

                    if url not in seen_urls:
                        seen_urls.add(url)
                        new_results.append({
                            "tool": getattr(msg, "name", "web_search"),
                            "title": data.get("title", ""),
                            "content": data.get("content", ""),
                            "url": url,
                            "score": data.get("score", 0.0)
                        })

            except Exception:
                content = content_str
                url_match = re.search(r'https?://\S+', content_str)

                if url_match:
                    url = url_match.group(0)

                    if url not in seen_urls:
                        seen_urls.add(url)
                        new_results.append({
                            "tool": getattr(msg, "name", "web_search"),
                            "title": "",
                            "content": content,
                            "url": url,
                            "score": 0.0
                        })

        if len(new_results) >= 8:
            break
    if not new_results and (state.tool_call_count or 0) > 0:
        return {
            "messages": [],
            "research_results": [],
            "research_summary": "No useful data could be retrieved.",
            "has_tool_calls": False,
            "tool_call_count": 0,
            "more_research_needed": False
        }
    new_results = sorted(new_results, key=lambda x: x["score"], reverse=True)[:5]

    if is_futile_context(new_results):
        return {
            "messages": [],
            "research_results": new_results,
            "research_summary": (
                "The requested information does not exist yet. "
                "This topic refers to a future or incomplete event, "
                "so no factual data is available."
            ),
            "has_tool_calls": False,
            "tool_call_count": 0,
            "more_research_needed": False
        }

    # ---------------------------
    # 🚨 4️⃣ TOOL CALL LIMIT GUARD
    # ---------------------------
    MAX_TOOL_CALLS = 8
    if state.tool_call_count and state.tool_call_count >= MAX_TOOL_CALLS:
        return {
            "messages": [],
            "research_results": new_results,
            "research_summary": (
                "Research stopped due to insufficient or unavailable data. "
                "Further tool calls are unlikely to provide new insights."
            ),
            "has_tool_calls": False,
            "tool_call_count": state.tool_call_count,
            "more_research_needed": False
        }

    # 2. Refined System Prompt: Directing the LLM's strategy
    for i, res in enumerate(new_results, start=1):
        snippet = " ".join(res["content"].split()[:50])
        search_history_context += f"""
            --- Source [{i}] ---
            Title: {res['title']}
            URL: {res['url']}
            Content: {snippet}
            Score: {res['score']}
            """

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

    clean_messages = [
        SystemMessage(content=system_prompt),
        *state.messages, # Include previous history
        HumanMessage(content=user_content)
    ]

    # 4. Invoke model
    response = await model_with_tools.ainvoke(clean_messages)

    # 5. Determine state updates for the LangGraph loop
    has_tool_calls = bool(response.tool_calls)

    previous_calls = state.tool_call_count or 0
    current_calls = len(response.tool_calls) if response.tool_calls else 0

    update = {
        "messages": [response],
        "research_results": new_results,
        "has_tool_calls": has_tool_calls,
        "tool_call_count": previous_calls + current_calls
    }

    # Signal if we need to stay in the research loop or proceed to writing
    if not response.tool_calls:
        update["research_summary"] = response.content
        update["more_research_needed"] = False
    else:
        update["more_research_needed"] = True

    return update