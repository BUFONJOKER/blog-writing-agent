from state import BlogAgentState
from pydantic import Field, BaseModel
from langchain_core.prompts import ChatPromptTemplate
from model.ollama import load_model
from typing import List

class ResearchQueryGenNodeOutput(BaseModel):
    """
    Structured output from the Research Query Generation node.

    This class enforces a multi-dimensional search strategy, ensuring the agent
    produces a diverse set of high-signal queries. These queries are used to
    populate the global state and drive the execution of MCP-enabled search tools
    (e.g., web_search_tool) to gather factual grounding for the blog post.
    """


    # 1. Research Queries: Optimized for Search Engine Retrieval
    research_queries: List[str] = Field(
        default_factory=list,
        description=(
            "A set of 3-5 distinct, targeted search strings. These must be optimized "
            "to retrieve factual data, technical specifications, and diverse perspectives "
            "from the web to provide a grounded foundation for the blog post."
        )
    )

    # 2. Research Gaps: The "Informational Audit"
    research_gaps: List[str] = Field(
        default_factory=list,
        description=(
            "A detailed list of specific topics, data points, or questions that remain "
            "unanswered after the initial research. This serves as an audit trail of "
            "what information is still missing to fulfill the requirements of the blog_plan."
        )
    )

    # 3. More Research Needed: The "Workflow Governor"
    more_research_needed: bool = Field(
        default=False,
        description=(
            "A boolean flag that triggers a recursive research loop. Set to True only if "
            "the research_gaps list contains critical information voids that prevent "
            "the agent from generating a high-quality, factually accurate draft."
        )
    )


def research_query_gen_node(state: BlogAgentState) -> dict:
    """
    Acts as the Senior Research Strategist to decompose the user prompt into a
    structured research roadmap.

    This node utilizes a Multi-Dimensional Search Strategy to generate 3-5
    high-signal, SEO-optimized search strings. These queries are specifically
    engineered to populate the `research_queries` field for downstream execution
    by MCP-enabled search tools (e.g., web_search_tool).

    The generation logic enforces four distinct silos:
    1. Technical Core: Architectural and theoretical definitions.
    2. Temporal Relevance: 2024-2026 trends and version-specific updates.
    3. Practicality: Implementation patterns and real-world case studies.
    4. Comparative Analysis: Competitive benchmarks and pros/cons.

    Args:
        state (BlogAgentState): The current global state, requiring the
            `prompt` and `metadata` fields for context.

    Returns:
        dict: A partial state update containing the `research_queries` list,
            ensuring the graph can transition to the researcher_node or
            research_loop.
    """

    model = load_model()

    llm_structured_output = model.with_structured_output(schema=ResearchQueryGenNodeOutput, method='function_calling')

    system_prompt = """
    You are an Expert Research Strategist for technical content and MLOps.
    Transform the user prompt into 3-5 high-signal search queries for MCP tools, minimizing noise and maximizing factual grounding.

    Search Strategy:
    1. Technical: architectures, algorithms, protocols, definitions.
    2. Temporal (2024-2026): latest updates, benchmarks, news.
    3. Practical: code patterns, deployment tips, tutorials.
    4. Comparative: competitors, pros/cons, benchmark comparisons.

    Output Requirements:
    - research_queries: 3-5 distinct, targeted search strings to retrieve factual data, technical specs, and diverse perspectives.
    - research_gaps: specific topics or questions still unanswered; an audit of missing info.
    - more_research_needed: boolean; True if critical gaps remain that prevent a complete, accurate draft.

    Constraints:
    - Output only structured data; no explanations or preamble.
    - SEO-optimized, keyword-dense, search-engine style.
    - Each query must cover a distinct silo; avoid redundancy.
    - Queries must work with web_search_tool and fetch_page_tool.

    Step: Identify knowledge gaps in the user prompt to guide query diversity.
    """



    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", '''Analyze the following user request and generate a Research Roadmap.

                USER REQUEST:
                ---
                {prompt}
                ---

                Generate 3-5 high-signal search queries that:
                1. Fill knowledge gaps in core technology.
                2. Include current (2024-2026) benchmarks or news.
                3. Find relevant code patterns or architectural best practices.

                Output must strictly follow the structured `research_queries` schema for web_search_tool.''')
    ])


    chain = prompt_template | llm_structured_output

    response: ResearchQueryGenNodeOutput = chain.invoke({"prompt": state.prompt})

    return {
        "research_queries": response.research_queries,
        "research_gaps": response.research_gaps,
        "more_research_needed": response.more_research_needed
    }




if __name__ == "__main__":
    # Example test case for the research query generation node
    test_state = BlogAgentState(
        prompt="Write a blog post about the latest updates in LangGraph and how it compares to LangChain for building AI agents."
    )

    output = research_query_gen_node(test_state)
    print(output)