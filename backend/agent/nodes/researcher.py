from agent.tools import initialize_tools
from langchain_core.prompts import ChatPromptTemplate
from agent.model.ollama import load_model
from agent.state import BlogAgentState
import asyncio

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
    tools = await initialize_tools(tools_place='local')

    tools_by_name = {tool.name: tool for tool in tools}

    allowed_tools = ["web_search_tool", "fetch_page_tool"]

    specific_tools = [tools_by_name[tool_name] for tool_name in allowed_tools if tool_name in tools_by_name]

    model = load_model()

    llm_with_tools = model.bind_tools(specific_tools)


    system_prompt = """
        You are a Lead Research Agent. Your goal is to gather high-fidelity, factual evidence for a technical blog post using a two-tier retrieval strategy.

        ### OPERATIONAL PROTOCOL:
        1. PHASE 1 (Broad Search): Execute `web_search` for every query provided in `state['research_queries']`. Analyze the snippets for relevance, authority, and data freshness.
        2. PHASE 2 (Deep Dive): Identify the top 2-3 most relevant URLs from the search results. Use `fetch_page` to retrieve the full text of these specific pages to extract nuanced details, statistics, and expert quotes.
        3. BUDGET CONTROL: You have a strict limit of 8 total tool calls. Monitor your progress and prioritize high-value sources as you approach this limit.
        4. STOP CRITERIA: Stop searching if:
        - You have found definitive answers for all research queries.
        - You have hit the 8-call maximum.
        - You have identified a conflict in facts that requires human intervention (status = 'error').

        ### CRITICAL CONSTRAINTS:
        - Do not re-search the same query twice.
        - If a `fetch_page` call fails (e.g., 404 or timeout), do not retry; move to the next best URL.
        - Focus only on technical accuracy and objective facts. Avoid promotional content or "fluff."
        """

    response = llm_with_tools.invoke(state.prompt)

    print(response)

if __name__ == "__main__":

    asyncio.run(researcher_node(BlogAgentState(prompt="name tools connected with you?")))