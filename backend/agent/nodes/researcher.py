from tools import initialize_tools
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from model.ollama import load_model
from state import BlogAgentState
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import asyncio
from typing import List

async def get_research_tools():
    tools = await initialize_tools(tools_place='local')

    tools_by_name = {tool.name: tool for tool in tools}

    allowed_tools = ["web_search_tool", "fetch_page_tool","extract_keywords_tool","summarize_research"]

    specific_tools = [tools_by_name[tool_name] for tool_name in allowed_tools if tool_name in tools_by_name]

    return specific_tools

async def researcher_node(state: BlogAgentState) -> dict:
    """Perform research based on the user's prompt and update the state with findings.

    This node is responsible for executing the research phase of the agent's workflow.
    It uses the search queries generated in the previous node to fetch relevant information
    using the tools registered in the MCP server. The results are then processed and
    stored in the state for use in later stages of planning and drafting.

    Args:
        state: Current graph state containing the user's prompt, routing decision, and generated search queries.

    Returns:
        A partial state dictionary with a new field `research_results` containing the aggregated findings from the research phase.
    """

    # Load tools from MCP server

    tools = await get_research_tools()

    model = load_model()

    llm_with_tools = model.bind_tools(tools)


    system_prompt = """
    You are the Lead Researcher for a technical blog post.

    Use tools in this order:
    1. web_search_tool → find URLs
    2. fetch_page_tool → get content
    3. summarize_research → summarize
    4. extract_keywords_tool → keywords

    Rules:
    - Do not repeat queries
    - Focus on factual, technical data
    - Stop when enough info is gathered
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),MessagesPlaceholder(variable_name="messages")
    ])

    chain = prompt | llm_with_tools

    research_queries = state.research_queries

    if not state.messages:
        state.messages = [HumanMessage(content=f"Research Query: {query}") for query in research_queries]

    response: AIMessage = await chain.ainvoke({"messages": state.messages})

    state.messages.append(response)

    research_results = [
        {
            "tool_name": getattr(msg, "name", ""),
            "tool_call_id": getattr(msg, "tool_call_id", ""),
            "content": msg.content,
        }
        for msg in state.messages
        if isinstance(msg, ToolMessage)
    ]

    tool_call_count = state.tool_call_count + len(response.tool_calls or [])

    research_summary = state.research_summary or ""

    if not response.tool_calls:
        research_summary = response.content

    return {
        "messages": state.messages,
        "research_results": research_results,
        "research_summary": research_summary,
        "tool_call_count": tool_call_count,
    }

if __name__ == "__main__":

    asyncio.run(researcher_node(BlogAgentState(prompt="name tools connected with you?")))