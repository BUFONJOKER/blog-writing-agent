from agent.state import BlogAgentState

def research_loop_node(state: BlogAgentState) -> dict:
    """
    Gate whether another external research cycle is needed.
    Acts as a safety valve for the iterative research process.
    """
    # 1. Pull the decision from the state (set by research_query_gen or researcher)
    need_more = bool(state.more_research_needed)

    # 2. Safety Check: Hard cap on tool usage to prevent API credit drain or infinite loops
    if state.tool_call_count >= state.max_tool_calls:
        print(f"--- MAX TOOL CALLS ({state.max_tool_calls}) REACHED: FORCING EXIT ---")
        need_more = False

    # 3. Logic: If we don't need more research, we should ensure the 'more_research_needed'
    # flag is set to False so the conditional edge in workflow.py routes to 'planner_node'.
    return {
        "more_research_needed": need_more,
        "status": "planning" if not need_more else "researching"
    }