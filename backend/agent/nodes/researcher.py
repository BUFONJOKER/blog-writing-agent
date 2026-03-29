from agent.tools import get_mcp_tools, initialize_tools
from langchain_core.prompts import ChatPromptTemplate
from agent.model.ollama import load_model
from agent.state import BlogAgentState

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
    tools = await initialize_tools()

    tools_by_name = {tool.name: tool for tool in tools}

    allowed_tools = ["web_search_tool", "fetch_page_tool"]

    specific_tools = [tools_by_name[tool_name] for tool_name in allowed_tools if tool_name in tools_by_name]

    model = load_model()

    llm_with_tools = model.bind_tools(specific_tools)

    response = llm_with_tools.invoke(state.prompt)

    print(response)

if __name__ == "__main__":
    import asyncio
    asyncio.run(researcher_node(BlogAgentState(prompt="name tools connected with you?")))