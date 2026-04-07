from langgraph.graph import StateGraph, START, END
from agent.state import BlogAgentState
# import all nodes
from agent.nodes.router import router_node
from agent.nodes.research_query_gen import research_query_gen_node
from agent.nodes.summarizer import summarizer_node
from agent.nodes.research_query_gen import research_query_gen_node
from agent.nodes.planner import planner_node
from agent.nodes.task_executer import task_executer_node
from agent.nodes.assembler import assembler_node
from agent.nodes.editor import editor_node
from agent.nodes.critic import critic_node
from agent.nodes.finalize import finalize_node
from agent.nodes.researcher import researcher_node
from agent.nodes.research_loop import research_loop_node
from agent.nodes.image_generation import image_generation_node
from agent.nodes.image_planner import image_planner_node

from langgraph.prebuilt import ToolNode
from agent.tools import initialize_tools
from functools import partial

async def build_workflow(checkpointer):
    graph = StateGraph(BlogAgentState)

    # Initialize shared tools (must include both web_search_tool and fetch_page_tool)
    shared_tools = await initialize_tools('local')

    # 1. Define Nodes
    researcher_tools_node = ToolNode(shared_tools)

    graph.add_node("router_node", router_node)
    # Pass tools to researcher so it can bind them to the LLM internally
    graph.add_node("researcher_node", partial(researcher_node, tools=shared_tools))
    graph.add_node("researcher_tools", researcher_tools_node)
    graph.add_node("research_query_gen_node", research_query_gen_node)
    graph.add_node("summarizer_node", summarizer_node)
    graph.add_node("research_loop", research_loop_node)
    graph.add_node("planner_node", planner_node)
    graph.add_node("task_executer_node", task_executer_node)
    graph.add_node("assembler_node", assembler_node)
    graph.add_node("editor_node", editor_node)
    graph.add_node("critic_node", critic_node)
    graph.add_node("finalize_node", finalize_node)
    graph.add_node("image_planner_node", image_planner_node)
    graph.add_node("image_generation_node", image_generation_node)

    # 2. Define Routing Logic
    graph.add_edge(START, "router_node")

    def route_research(state: BlogAgentState):
        if state.needs_research:
            return "research_query_gen_node"
        return "summarizer_node"

    graph.add_conditional_edges("router_node", route_research, {
        "research_query_gen_node": "research_query_gen_node",
        "summarizer_node": "summarizer_node"
    })


    def should_execute_tools(state: BlogAgentState):
    # Ensure has_tool_calls is checked accurately
        if state.has_tool_calls and (state.tool_call_count or 0) < (state.max_tool_calls or 8):
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
        if state.more_research_needed:
            return "router_node"
        return "planner_node"

    graph.add_conditional_edges("research_loop", needs_research_loop, {
        "router_node": "router_node",
        "planner_node": "planner_node"
    })

    def needs_revision(state: BlogAgentState):
        if state.needs_revision and state.revision_cycles<=3:
            return "task_executer_node"
        return "finalize_node"

    graph.add_conditional_edges("critic_node", needs_revision, {
        "task_executer_node": "task_executer_node",
        "finalize_node": "finalize_node"
    })

    # Linear flow for remaining nodes
    graph.add_edge("research_query_gen_node", "researcher_node")
    graph.add_edge("summarizer_node", "research_loop")
    graph.add_edge("planner_node", "task_executer_node")
    graph.add_edge("task_executer_node", "assembler_node")
    graph.add_edge("assembler_node", "editor_node")
    graph.add_edge("editor_node", "critic_node")
    graph.add_edge("finalize_node", "image_planner_node")
    graph.add_edge("image_planner_node", "image_generation_node")
    graph.add_edge("image_generation_node", END)

    workflow = graph.compile(checkpointer=checkpointer, interrupt_after=['finalize_node'])
    return workflow

# write code to run this file and save the workflow image as workflow.png
# code to save to workflow image
# if __name__ == "__main__":
#     import asyncio

#     async def main():
#         workflow = await build_workflow(checkpointer=None)
#         png_bytes = workflow.get_graph().draw_mermaid_png()  # Uses Mermaid.ink (online, no deps)
#         with open("workflow.png", "wb") as f:
#             f.write(png_bytes)
#         print("Saved workflow.png")

#     asyncio.run(main())