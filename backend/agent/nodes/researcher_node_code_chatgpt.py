# researcher_node.py
import asyncio
from typing import Any, List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage
from state import BlogAgentState
from model.ollama import load_model
from tools import initialize_tools

async def researcher_node(state: BlogAgentState) -> dict:
    """
    Tool Powerhouse Research Node ⭐

    Executes real-world research using MCP tools.

    Flow:
    queries → web_search → urls → fetch_page → content → summarize → keywords

    Updates state:
    - research_results
    - research_summary
    """

    # 1️⃣ Initialize MCP tools
    tools = await initialize_tools(tools_place='local')
    tools_by_name = {tool.name: tool for tool in tools}
    allowed_tools = ["web_search_tool", "fetch_page_tool", "summarize_research", "extract_keywords_tool"]
    specific_tools = [tools_by_name[tool_name] for tool_name in allowed_tools if tool_name in tools_by_name]

    # 2️⃣ Load LLM and bind tools
    model = load_model()
    llm_with_tools = model.bind_tools(specific_tools)

    # 3️⃣ Build prompt with placeholder for multi-turn tool calls
    prompt = ChatPromptTemplate.from_messages([
        ("system", """
You are the Lead Researcher for a technical blog post. Your goal is to gather
high-fidelity, factual evidence using MCP tools.

### TOOL FLOW:
1. Run web_search_tool(query) for each research query.
2. Fetch full pages from top URLs using fetch_page_tool(url).
3. Summarize content via summarize_research(content).
4. Extract SEO keywords via extract_keywords_tool(summary).

### RULES:
- Limit total tool calls to 8.
- Do not search the same query twice.
- Skip failed fetch_page_tool calls.
- Stop if all queries answered or conflicting facts arise (status='error').

Research queries: {research_queries}
"""),
        MessagesPlaceholder(variable_name="messages"),
    ])

    chain = prompt | llm_with_tools

    research_queries: List[str] = state.research_queries or [state.prompt]
    messages: List[Any] = [HumanMessage(content=f"Research these queries: {research_queries}")]
    max_tool_calls = 8
    tool_call_count = 0
    research_results = []  # To store each tool result

    while tool_call_count < max_tool_calls:
        # 4️⃣ Invoke LLM
        response: AIMessage = await chain.ainvoke({
            "research_queries": research_queries,
            "messages": messages
        })
        messages.append(response)

        # 5️⃣ Check tool calls from LLM
        if not getattr(response, "tool_calls", []):
            # No more tools requested — finish
            final_summary = response.content or "Research complete."
            return {
                "research_results": research_results,
                "research_summary": final_summary,
                "research_status": "complete"
            }

        # 6️⃣ Execute tool calls
        for tool_call in response.tool_calls:
            tool_call_count += 1
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            if tool_call_count > max_tool_calls:
                break

            if tool_name not in tools_by_name:
                tool_result = f"Tool {tool_name} not available."
            else:
                try:
                    # Execute the requested tool
                    tool_result = await tools_by_name[tool_name].ainvoke(tool_args)
                    research_results.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": str(tool_result)
                    })
                except Exception as e:
                    tool_result = f"Tool error: {str(e)}"

            # 7️⃣ Append tool output to conversation
            messages.append(ToolMessage(
                content=str(tool_result),
                tool_call_id=tool_call["id"]
            ))

    # 8️⃣ Max tool calls reached
    summary = "Research truncated at max tool calls. Key findings: " + "; ".join([r["result"][:100] for r in research_results])
    return {
        "research_results": research_results,
        "research_summary": summary
    }


# Example usage
if __name__ == "__main__":
    import asyncio
    from state import BlogAgentState

    test_state = BlogAgentState(
        prompt="Write a blog post about Python 3.13 JIT compiler improvements and comparisons with 3.12."
    )
    result = asyncio.run(researcher_node(test_state))
    print(result)