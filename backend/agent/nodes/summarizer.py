from agent.state import BlogAgentState
from agent.tools import initialize_tools
import asyncio
from agent.model import load_model
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from typing import Dict, Any

async def summarizer_node(state: BlogAgentState) -> dict:
    # 1. Setup
    results = state.research_summary if state.needs_research else state.prompt
    topic = state.topic

    tools = await initialize_tools('local')
    model = load_model()
    llm_with_tools = model.bind_tools(tools, tool_choice="summarize_research")

    # 2. FIRST PASS: Get the "Directive" from the tool
    # We pass the raw data into the tool to get the formatted Instruction Block
    tool_call_response = await llm_with_tools.ainvoke(
        f"Use the summarize_research tool for the topic '{topic}' using this data: {results}"
    )

    directive = ""
    if tool_call_response.tool_calls:
        tool_call = tool_call_response.tool_calls[0]
        tool = next(t for t in tools if t.name == tool_call['name'])
        # This executes the python function in summarizer.py
        directive = await tool.ainvoke(tool_call['args'])

    print("Directive from tool:", directive)

    # 3. SECOND PASS: Use the Directive to generate the actual Summary
    # Now we feed the instructions returned by the tool BACK to the LLM
    final_summary_response = await model.ainvoke([
        ("system", "You are a Senior Technical Lead. Follow the directive provided by the user exactly."),
        ("human", directive) # The 'directive' contains the instructions + raw data
    ])

    # print(final_summary_response)

    # 4. Return the final text content
    return {
        "research_summary": final_summary_response.content,
        "messages": [tool_call_response, final_summary_response]
    }

if __name__ == "__main__":
    # Test state - add needs_research=True for real test
    state = BlogAgentState(
        prompt="What is AI? Research: AI is artificial intelligence involving machine learning.",
        needs_research=False  # Set True to test research_summary path
    )
    result = asyncio.run(summarizer_node(state))
