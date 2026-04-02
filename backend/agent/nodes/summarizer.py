from agent.state import BlogAgentState
import asyncio
from agent.model import load_model
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

async def summarizer_node(state: BlogAgentState) -> dict:
    model = load_model()
    # 1. Determine the source of data
    if state.needs_research:
        # Use research gathered from the web
        source_data = state.research_summary
    else:
        # Use internal model knowledge for general topics
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a Senior Technical Lead. Your task is to provide a concise, "
                "high-quality summary of the following topic based on your internal knowledge. "
                "Focus on key insights and technical accuracy."
            )),
            ("human", "Topic: {topic}\n\nProvide a summary based on your knowledge.")
        ])

        chain = prompt | model
        response = await chain.ainvoke({"topic": state.topic})
        source_data = response.content
    # 2. Define the Summarization Prompt
    # We combine the system role and the data in one template
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a Senior Technical Lead. Your task is to provide a concise, "
            "high-quality summary of the following data for a blog post. "
            "Focus on key insights and technical accuracy."
        )),
        ("human", "Topic: {topic}\n\nData to summarize: {data}")
    ])

    # 3. Generate Summary directly via LLM
    chain = prompt_template | model

    final_response = await chain.ainvoke({
        "topic": state.topic,
        "data": source_data
    })

    # 4. Prepare messages for state tracking
    # We store the final summary as an AIMessage
    ai_msg = AIMessage(content=final_response.content)

    return {
        "research_summary": final_response.content,
        "messages": [ai_msg]
    }

if __name__ == "__main__":
    # Test execution
    state = BlogAgentState(
        prompt="Explain the benefits of AI in 2026.",
        topic="Artificial Intelligence",
        needs_research=False,
        research_summary="AI has automated 40% of manual data entry tasks by 2026."
    )
    result = asyncio.run(summarizer_node(state))
    print(f"Summary: {result['research_summary']}")