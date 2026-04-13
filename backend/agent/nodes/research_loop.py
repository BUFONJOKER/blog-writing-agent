from agent.state import BlogAgentState


def research_loop_node(state: BlogAgentState) -> dict:
    """Decide whether the workflow should keep researching or move on.

    Args:
        state: Current workflow state containing research progress flags.

    Returns:
        dict: Updated loop decision and coarse workflow status.
    """
    # 1. Pull the decision from the state (set by research_query_gen or researcher)
    need_more = bool(state.more_research_needed)

    # 2. Safety Check: Hard cap on tool usage to prevent API credit drain or infinite loops
    if state.tool_call_count >= state.max_tool_calls:
        # print(f"--- MAX TOOL CALLS ({state.max_tool_calls}) REACHED: FORCING EXIT ---")
        need_more = False

    return {
        "more_research_needed": need_more,
        "status": "planning" if not need_more else "researching",
    }
