from langgraph.graph.state import StateGraph, START, END
from state import BlogAgentState
from nodes.router import router_node
from nodes.summarizer import summarizer_node
from nodes.research_query_gen import research_query_gen_node
from nodes.planner import planner_node
from nodes.task_executer import task_executer_node
from nodes.assembler import assembler_node
from nodes.editor import editor_node
from nodes.finalize import finalize_node
from nodes.critic import critic_node
from nodes.research_loop import research_loop_node
from nodes.researcher import researcher_node, get_research_tools
from langgraph.prebuilt import ToolNode

async def build_workflow():
    graph = StateGraph(BlogAgentState)

    tools = await get_research_tools()
    # nodes
    graph.add_node("router_node",router_node)
    graph.add_node("researcher_node", researcher_node)
    graph.add_node("researcher_tools", ToolNode(tools))
    graph.add_node("research_query_gen_node",research_query_gen_node)
    graph.add_node("summarizer_node", summarizer_node)
    graph.add_node("research_loop",research_loop_node)
    graph.add_node("planner_node", planner_node)
    graph.add_node("task_executer_node", task_executer_node)
    graph.add_node("assembler_node", assembler_node)
    graph.add_node("editor_node", editor_node)
    graph.add_node("critic_node", critic_node)
    graph.add_node("finalize_node", finalize_node)

    # edges
    graph.add_edge(START, "router_node")

    # conditional edges with their functions
    def route_research(state:BlogAgentState):
        if state.needs_research:
            return "research_query_gen_node"
        else:
            return "summarizer_node"

    graph.add_conditional_edges("router_node", route_research,
                                {
                                    "research_query_gen_node": "research_query_gen_node",
                                    "summarizer_node": "summarizer_node"
                                })

    def needs_revision(state:BlogAgentState):
        if state.needs_revision:
            return "task_executer_node"
        else:
            return "finalize_node"

    def needs_research(state:BlogAgentState):
        if state.more_research_needed:
            return "router_node"
        else:
            return "planner_node"

    def should_execute_tools(state: BlogAgentState):
        last_message = state.messages[-1] if state.messages else None
        has_tool_calls = bool(getattr(last_message, "tool_calls", None))
        under_cap = state.tool_call_count < state.max_tool_calls
        if has_tool_calls and under_cap:
            return "researcher_tools"
        return "summarizer_node"

    graph.add_conditional_edges("critic_node", needs_revision,
                                {
                                    "task_executer_node": "task_executer_node",
                                    "finalize_node": "finalize_node"
                                })

    graph.add_conditional_edges("research_loop", needs_research, {
        "router_node": "router_node",
        "planner_node": "planner_node"
    })

    graph.add_conditional_edges(
        "researcher_node",
        should_execute_tools,
        {
            "researcher_tools": "researcher_tools",
            "summarizer_node": "summarizer_node",
        },
    )


    # other edges
    graph.add_edge("research_query_gen_node", "researcher_node")
    graph.add_edge("researcher_tools", "researcher_node")
    graph.add_edge("summarizer_node", "research_loop")
    graph.add_edge("research_loop", "planner_node")
    graph.add_edge("planner_node", "task_executer_node")
    graph.add_edge("task_executer_node", "assembler_node")
    graph.add_edge("assembler_node", "editor_node")
    graph.add_edge("editor_node",'critic_node')
    graph.add_edge("critic_node", "finalize_node")
    graph.add_edge("finalize_node",END)

    workflow = graph.compile()

    return workflow


# import asyncio

# async def save_graph_image():
#     # 1. Build the workflow
#     workflow = await build_workflow()

#     # 2. Generate the PNG bytes
#     # Note: This requires the 'pyppeteer' or 'graphviz' dependencies
#     # usually installed via `pip install langchain-core[draw]`
#     png_bytes = workflow.get_graph().draw_mermaid_png()

#     # 3. Write to a file
#     with open("workflow.png", "wb") as f:
#         f.write(png_bytes)
#     print("Workflow saved as workflow.png")


# if __name__ == "__main__":
#     # Run the async function
#     asyncio.run(save_graph_image())