from model.ollama import load_model
from state import BlogAgentState
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

class RouterNodeDecision(BaseModel):
    """Structured router output returned by the LLM classifier.

    The class defines the single routing decision used by the graph to choose
    whether a research phase should run before planning and drafting.
    """

    # Changed from Literal strings to a boolean for direct logic use
    needs_research: bool = Field(
    default=False,
    description=(
        "Set to True if the prompt requires real-time information, current events, "
        "specific factual grounding (e.g., statistics, technical documentation), or "
        "data beyond the model's knowledge cutoff. Set to False if the request "
        "is creative, general-purpose, or can be fulfilled using the model's "
        "existing internal knowledge."
    )
)

def router_node(state: BlogAgentState) -> dict:
    """Classify the incoming prompt and return a routing state update.

    Args:
        state: Current graph state containing the user's prompt.

    Returns:
        A partial state dictionary with the `needs_research` flag set to the
        model's classification result.
    """

    model = load_model()
    # Using 'tool_calling' is often more robust for Ollama models than 'function_calling'
    llm_structured_output = model.with_structured_output(schema=RouterNodeDecision,method='function_calling')

    system_prompt = """
        You are an expert Content Strategy Router. Your sole objective is to analyze a user's blog request and determine if the agent must perform external research.

        ### CRITERIA FOR RESEARCH (needs_research = True):
        1. CURRENT EVENTS: The topic involves news, sports results (e.g., ICC Trophy), or recent tech releases.
        2. SPECIFIC FACTS: The user asks for statistics, technical benchmarks, or specific data points.
        3. UNFAMILIAR ENTITIES: The prompt mentions specific companies, people, or niche tools (like MCP, LangGraph, or specific Python libraries).
        4. RECENT TRENDS: Any topic where information from 2024-2026 is required for accuracy.

        ### CRITERIA FOR NO RESEARCH (needs_research = False):
        1. GENERAL KNOWLEDGE: Common topics like "How to stay healthy" or "The history of the Roman Empire."
        2. CREATIVE WRITING: Requests for poems, fictional stories, or personal reflections.
        3. LOGICAL/MATH TASKS: Coding syntax explanations or basic logic problems that don't require external API data.

        ### FINAL INSTRUCTION:
        If you are even 1% unsure, set 'needs_research' to True to ensure factual accuracy.
        """

    # It's better to pass the prompt directly to the template
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "User Prompt: {prompt}")
    ])

    chain = prompt_template | llm_structured_output

    # We pass only the prompt field from the state
    response = chain.invoke({"prompt": state.prompt})

    return {
        "needs_research": response.needs_research
    }


# only for testing purposes, not part of the actual graph execution

if __name__ == "__main__":
    import asyncio
    import time
    async def test_router():
        test_prompts = [
            # Timeless / No Research Needed
            "Write a poem about a lonely robot in space.",
            "Explain the concept of 'hoisting' in JavaScript.",

            # Current Events / Research Needed
            "Who won the 2024 ICC Champions Trophy and what was the final score?",
            "What are the latest features released in LangGraph as of March 2026?",
            "Summarize the performance of the Pakistan cricket team in their last series."
        ]

        print(f"\n{'Prompt':<60} | {'Needs Research':<15}")
        print("-" * 80)

        for p in test_prompts:
            # Initialize state with the updated schema
            state = BlogAgentState(prompt=p)

            start_time = time.time()
            result = router_node(state)
            end_time = time.time()
            print(f"Time taken: {end_time - start_time:.2f}s") # Verify if < 2.00s

            # Print results for verification
            print(f"{p[:58]:<60} | {str(result['needs_research']):<15}")

    asyncio.run(test_router())