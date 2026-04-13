from langgraph.graph import StateGraph, START, END
from agent.state import BlogAgentState

# import all nodes
from agent.nodes.router import router_node
from agent.nodes.research_query_gen import research_query_gen_node
from agent.nodes.summarizer import summarizer_node
from agent.nodes.planner import planner_node
from agent.nodes.task_executer import task_executer_node
from agent.nodes.assembler import assembler_node
from agent.nodes.editor import editor_node
from agent.nodes.critic import critic_node
from agent.nodes.finalize import finalize_node
from agent.nodes.researcher import researcher_node
from agent.nodes.research_loop import research_loop_node

from langgraph.prebuilt import ToolNode
from functools import partial
from langgraph.types import interrupt
from functools import partial


async def build_workflow(checkpointer, model, shared_tools):
    """Build and compile the LangGraph workflow for blog generation.

    Args:
        checkpointer: LangGraph checkpointer used to persist run state.
        model: Language model instance used by the graph nodes.
        shared_tools: Tool list exposed to the research and drafting nodes.

    Returns:
        Any: The compiled workflow graph ready for execution.
    """
    graph = StateGraph(BlogAgentState)

    # 1. Define Nodes
    researcher_tools_node = ToolNode(shared_tools)

    async def human_review_node(state: BlogAgentState):
        """Pause execution and wait for a human approval decision.

        Args:
            state: Current workflow state containing the draft and feedback.

        Returns:
            dict: Human approval flag used to route the workflow forward.
        """
        approved = interrupt(
            value={
                "feedback": state.critic_feedback,
                "draft": state.edited_draft,
            }
        )
        return {"human_approved": bool(approved)}

    # ✅ FIXED: Consistent node name
    graph.add_node("human_review", human_review_node)

    graph.add_node(
        "router_node", partial(router_node, model=model)
    )  # Pass model to router for classification
    # Pass tools to researcher so it can bind them to the LLM internally
    graph.add_node(
        "researcher_node", partial(researcher_node, tools=shared_tools, model=model)
    )
    graph.add_node("researcher_tools", researcher_tools_node)
    graph.add_node(
        "research_query_gen_node", partial(research_query_gen_node, model=model)
    )
    graph.add_node("summarizer_node", partial(summarizer_node, model=model))
    graph.add_node("research_loop", research_loop_node)
    graph.add_node("planner_node", partial(planner_node, model=model))
    graph.add_node("task_executer_node", partial(task_executer_node, model=model))
    graph.add_node("assembler_node", partial(assembler_node, model=model))
    graph.add_node("editor_node", partial(editor_node, model=model))
    graph.add_node("critic_node", partial(critic_node, model=model))
    graph.add_node("finalize_node", partial(finalize_node, model=model))

    # 2. Define Routing Logic
    graph.add_edge(START, "router_node")

    def route_research(state: BlogAgentState):
        """Route the workflow to research or summarization based on state.

        Args:
            state: Current workflow state containing the research decision.

        Returns:
            str: The next node name to execute.
        """
        if state.needs_research:
            return "research_query_gen_node"
        return "summarizer_node"

    graph.add_conditional_edges(
        "router_node",
        route_research,
        {
            "research_query_gen_node": "research_query_gen_node",
            "summarizer_node": "summarizer_node",
        },
    )

    def should_execute_tools(state: BlogAgentState):
        """Decide whether the researcher should invoke tools again.

        Args:
            state: Current workflow state including tool call counters.

        Returns:
            str: The next node name for the researcher branch.
        """
        # Ensure has_tool_calls is checked accurately
        if state.has_tool_calls and (state.tool_call_count or 0) < (
            state.max_tool_calls or 8
        ):
            return "researcher_tools"

        # If the researcher_node returned False for has_tool_calls,
        # it means the LLM provided a final text response.
        return "summarizer_node"

    # 3. Add the Researcher -> Tools -> Researcher Loop
    graph.add_conditional_edges(
        "researcher_node",
        should_execute_tools,
        {
            "researcher_tools": "researcher_tools",
            "summarizer_node": "summarizer_node",
        },
    )

    # IMPORTANT: After tools run, we MUST go back to the researcher
    # so it can process the search results/page content.
    graph.add_edge("researcher_tools", "researcher_node")

    def needs_research_loop(state: BlogAgentState):
        """Route back into research when additional facts are needed.

        Args:
            state: Current workflow state containing the research loop flag.

        Returns:
            str: The next node name to execute.
        """
        if state.more_research_needed:
            return "router_node"
        return "planner_node"

    graph.add_conditional_edges(
        "research_loop",
        needs_research_loop,
        {"router_node": "router_node", "planner_node": "planner_node"},
    )

    def route_after_human(state: BlogAgentState):
        """Route after human review based on approval and revision count.

        Args:
            state: Current workflow state containing approval and revision data.

        Returns:
            str: The next node name to execute after review.
        """
        if state.human_approved:
            return "finalize_node"
        elif state.revision_cycles < 3:
            return "task_executer_node"
        else:
            return "finalize_node"

    graph.add_conditional_edges(
        "human_review",  # ✅ Matches add_node name
        route_after_human,
        {
            "task_executer_node": "task_executer_node",
            "finalize_node": "finalize_node",
        },
    )

    # Linear flow for remaining nodes
    graph.add_edge("research_query_gen_node", "researcher_node")
    graph.add_edge("summarizer_node", "research_loop")
    graph.add_edge("planner_node", "task_executer_node")
    graph.add_edge("task_executer_node", "assembler_node")
    graph.add_edge("assembler_node", "editor_node")
    graph.add_edge("editor_node", "critic_node")
    graph.add_edge("critic_node", "human_review")  # ✅ To human_review (not _node)
    graph.add_edge("finalize_node", END)

    # HIL is temporarily disabled until the interactive review flow is fully implemented.
    workflow = graph.compile(checkpointer=checkpointer)
    return workflow


# write code to generate image of workflow using graph mermaid png and save to png file
if __name__ == "__main__":
    import asyncio

    async def main():
        """Render the workflow graph to a Mermaid PNG for local inspection.

        Args:
            None: This debug helper constructs a sample workflow only.

        Returns:
            None: The graph image is written to disk.
        """
        app = await build_workflow(checkpointer=None, model=None, shared_tools=[])
        graph_png_bytes = app.get_graph().draw_mermaid_png()
        # 2. Save to a file
        with open("blog_agent_workflow.png", "wb") as f:
            f.write(graph_png_bytes)

        print("✅ Workflow saved as blog_agent_workflow.png")

    asyncio.run(main())
