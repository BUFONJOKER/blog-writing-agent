from state import BlogAgentState


def research_loop_node(state: BlogAgentState) -> dict:
    """Gate whether another external research cycle is needed."""
    need_more = bool(state.more_research_needed)

    if state.tool_call_count >= state.max_tool_calls:
        need_more = False

    return {"more_research_needed": need_more}