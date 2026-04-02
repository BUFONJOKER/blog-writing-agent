import asyncio
from typing import List
from langchain_core.messages import AIMessage, ToolMessage, SystemMessage, HumanMessage
from agent.state import BlogAgentState
from agent.model import load_model

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

    for msg in state.messages:
        if isinstance(msg, ToolMessage):
            # Ensure content is a string
            content_str = msg.content
            if isinstance(content_str, list):
                # Extract text if it's a list of blocks
                content_str = content_str[0].get("text", str(content_str)) if content_str else ""

            # Create the dictionary that matches your State's List[dict] requirement
            result_entry = {
                "tool": getattr(msg, "name", "web_search"),
                "content": content_str,
                "url": msg.additional_kwargs.get("url", "N/A") # Optional: capture URL if available
            }

            new_results.append(result_entry)
            search_history_context += f"\n--- Previous Tool Output ---\n{content_str}\n"

    # 2. Refined System Prompt: Directing the LLM's strategy
    system_prompt = (
        "You are a Senior Research Assistant. Your goal is to gather deep, factual information.\n\n"
        "STRATEGY:\n"
        "1. Initial Phase: Use 'web_search_tool' to find authoritative source URLs.\n"
        "2. Extraction Phase: If search snippets are brief or generic, identify the most promising URL "
        "and use 'fetch_page_tool' to extract the full article content. High-quality blogs require "
        "deep text extraction, not just snippets.\n\n"
        "CRITICAL RULE: When calling 'web_search_tool', you MUST ONLY provide the 'query' argument.\n"
        "CRITICAL RULE: When calling 'fetch_page_tool', you MUST provide both the 'url' (from your search results) "
        "and a 'query' to focus the extraction."
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
        HumanMessage(content=user_content)
    ]

    # 4. Invoke model
    response = await model_with_tools.ainvoke(clean_messages)

    # 5. Determine state updates for the LangGraph loop
    has_tool_calls = bool(response.tool_calls)

    update = {
        "messages": [response],
        "research_results": new_results, # Now correctly passes List[dict] validation
        "has_tool_calls": bool(response.tool_calls),
        "tool_call_count": len(response.tool_calls) if response.tool_calls else 0
    }

    # Signal if we need to stay in the research loop or proceed to writing
    if not response.tool_calls:
        update["research_summary"] = response.content
        update["more_research_needed"] = False
    else:
        update["more_research_needed"] = True

    return update