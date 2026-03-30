from state import BlogAgentState
from pydantic import Field, BaseModel
from langchain_core.prompts import ChatPromptTemplate
from model.ollama import load_model

class ResearchQueryGenNodeOutput(BaseModel):
    """Structured output from the research query generation node.

    This class defines the expected output format for the node that generates
    search queries based on the user's prompt. The `research_queries` field is
    a list of strings, where each string is a distinct search query intended
    to retrieve relevant information for the blog post.
    """

    research_queries: list[str] = Field(
        description="A list of search queries generated from the user's prompt to guide the research phase."
    )

def research_query_gen_node(state: BlogAgentState) -> dict:
    """Generate search queries based on the user's prompt.

    This node takes the original user prompt and produces a set of search queries
    that can be used to gather relevant information during the research phase. The
    generated queries should be specific enough to retrieve useful results but
    broad enough to cover different aspects of the topic.

    Args:
        state: Current graph state containing the user's prompt and routing decision.

    Returns:
        A partial state dictionary with the `research_queries` field populated based
        on the analysis of the prompt.
    """

    model = load_model()
    llm_structured_output = model.with_structured_output(schema=ResearchQueryGenNodeOutput, method='function_calling')

    system_prompt = """
    You are a Senior Research Strategist for a high-quality technical blog.
    Your goal is to transform a single user request into a set of 3-5 distinct,
    high-intent search queries.

    ### SEARCH STRATEGY:
    1. TECHNICAL CORE: One query focusing on the underlying technology or definitions.
    2. CURRENT ECOSYSTEM: One query focusing on 2024-2026 trends, updates, or news.
    3. PRACTICAL USE: One query looking for real-world examples, tutorials, or case studies.
    4. COMPARATIVE: One query looking for pros/cons or comparisons with similar tools.

    ### CONSTRAINTS:
    - Do not use filler words like "find info about..."
    - Use keyword-rich phrases optimized for search engines.
    - Ensure queries are distinct; avoid overlapping search results.
    """



    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", '''The user wants to write a blog post based on this specific request:
        ---
        {prompt}
        ---
        Based on the criteria above, generate exactly 3-5 search queries that will
        provide the necessary factual grounding for this article.''')
    ])

    chain = prompt_template | llm_structured_output

    response = chain.invoke({"prompt": state.prompt})

    return {
        "research_queries": response.research_queries
    }


# code to test the node in isolation --- IGNORE ---
if __name__ == "__main__":
    import asyncio
    import time

    async def run_research_benchmark():
        # A difficult set of 10 prompts to stress-test logic and speed
        test_prompts = [
            "Analyze how 2024-2026 AI regulation in the EU, US, and China impacts open-source LLM startups; include compliance cost estimates and GTM implications.",
            "Compare LangGraph, AutoGen, and CrewAI for production multi-agent orchestration with fault tolerance, checkpointing, and human-in-the-loop controls in 2026.",
            "Evaluate whether retrieval-augmented generation or long-context models perform better for legal contract analysis, citing benchmark trends from 2024-2026.",
            "Assess the macroeconomic and semiconductor supply-chain effects of post-2024 Bitcoin halving cycles on GPU pricing, AI datacenter demand, and energy markets.",
            "Design a migration strategy from monolithic FastAPI to event-driven microservices for an AI content platform with SLO targets, rollback plans, and risk matrix.",
            "Investigate breakthroughs in solid-state batteries from 2023-2026 and quantify commercialization barriers across materials, manufacturing yield, and charging infrastructure.",
            "Critically compare 'uv', Poetry, and pip-tools for secure Python dependency management in enterprise CI/CD, including lockfile reproducibility and SBOM workflows.",
            "Build a research-backed argument on whether AI copilots improve senior developer productivity, separating measured outcomes from self-reported survey bias.",
            "Map the technical and policy trade-offs of on-device LLMs vs cloud inference for healthcare assistants, including privacy law constraints and model update latency.",
            "Produce a comparative analysis of autonomous web agents in 2026, covering browser control reliability, tool-use planning, hallucination mitigation, and eval frameworks."
        ]

        print(f"\n{'#':<3} | {'Latency':<8} | {'Queries':<7} | {'Prompt Preview'}")
        print("-" * 85)

        total_time = 0
        success_count = 0

        for i, p in enumerate(test_prompts, 1):
            # 1. Initialize State
            state = BlogAgentState(prompt=p)

            # 2. Start High-Resolution Timer
            start = time.perf_counter()
            try:
                result = research_query_gen_node(state)
                end = time.perf_counter()

                latency = end - start
                total_time += latency
                queries = result.get("research_queries", [])
                count = len(queries)

                # 3. Performance & Logic Marking
                # Target: < 2.0s and 4-6 queries
                is_fast = latency < 2.0
                is_correct_count = 4 <= count <= 6

                icon = "✅" if is_fast and is_correct_count else "⚠️"
                if not is_fast: icon = "🐢"

                if is_correct_count: success_count += 1

                print(f"{i:<3} | {latency:>6.2f}s {icon} | {count:<7} | {p[:45]}...")
                print("      Generated Queries:")
                if queries:
                    for idx, query in enumerate(queries, 1):
                        print(f"        {idx}. {query}")
                else:
                    print("        (no queries returned)")
                print("-" * 85)

            except Exception as e:
                print(f"{i:<3} | FAILED   | 0       | Error: {str(e)[:40]}...")

        # 4. Final Summary
        avg_time = total_time / len(test_prompts)
        print("-" * 85)
        print(f"SUMMARY:")
        print(f"- Average Latency: {avg_time:.2f}s (Target: < 2.0s)")
        print(f"- Accuracy Score:  {success_count}/{len(test_prompts)} prompts met query count target.")

    # Run the benchmark in your WSL2 terminal
    asyncio.run(run_research_benchmark())