from agent.state import BlogAgentState
from agent.model import load_model
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from typing import List

class SectionPlan(BaseModel):
    description: str = Field(description="A brief description of the section's content and purpose")

    word_count: str = Field(description="Approximate word count for the section")

    key_points: List[str] = Field(description="Bullet points outlining the main ideas to cover in the section")

    seo_keywords: List[str] = Field(description="Relevant SEO keywords to include in the section")

    estimated_total_words: int = Field(description="Estimated total word count for the section")

class BlogPlan(BaseModel):
    title: str = Field(description="The title of the blog post")

    subtitile: str = Field(description="The subtitle of the blog post")

    tone: str = Field(description="The tone of the blog post (e.g., formal, conversational, technical)")

    audience: str = Field(description="The target audience for the blog post (e.g., developers, CTOs, general tech enthusiasts)")

    tasks: List[str] = Field(description="List of section-level writing tasks derived from the outline")

    sections: List[SectionPlan] = Field(description="Detailed plan for each section of the blog post")


def planner_node(state: BlogAgentState):

    prompt = state.prompt

    research_summary = state.research_summary

    system_prompt = """
    You are a Senior Content Strategist and SEO Expert specializing in high-growth technical blogs.
    Your objective is to transform raw research into a comprehensive "Content Blueprint" that a technical writer can follow with zero ambiguity.

    ### STRATEGIC OBJECTIVES:
    1. CONTENT ARCHITECTURE: Create a logical narrative flow (Hook -> Problem -> Solution -> Technical Deep-Dive -> Actionable Conclusion).
    2. DATA-DRIVEN PLANNING: Every 'key_point' must be backed by the 'research_summary'. Do not hallucinate trends; stick to the provided data.
    3. SEO INTEGRATION: Identify primary and secondary keywords relevant to the 2026 tech landscape. Distribute them naturally across section plans.
    4. PRECISION SCOPING: Assign 'word_count' targets that reflect the complexity of the section (e.g., deeper counts for the 'Technical Deep-Dive').

    ### STRUCTURAL REQUIREMENTS:
    - TITLE & SUBTITLE: Must be punchy, benefit-driven, and include at least one primary SEO keyword.
    - SECTIONS: Ensure there is a clear distinction between the purpose of each section.
    - KEY POINTS: Provide at least 3-5 specific bullet points per section to ensure depth.
    - TASKS: Write these as clear directives for the next agent (e.g., "Draft the Technical Deep-Dive focusing on edge device integration metrics").

    ### FINAL AUDIT:
    Before finalizing, ensure the 'estimated_total_words' across all sections aligns with the user's expected blog length (default to 1000-1500 words if unspecified).
    """

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Based on the following prompt {prompt} and a research summary\n {research_summary} create a detailed blog plan.")
    ])

    model = load_model()

    model_with_structured_output = model.with_structured_output(schema=BlogPlan, method='function_calling')

    chain = prompt_template | model_with_structured_output

    response = chain.invoke({
        "prompt": prompt,
        "research_summary": research_summary
    })

    ai_msg = AIMessage(
    content=(
        f"Successfully generated a blog plan titled: '{response.title}'.\n"
        f"Target Audience: {response.audience}\n"
        f"Tone: {response.tone}\n"
        f"Structure: {response.sections} sections with a {response.tasks} writing tasks."
        )
    )
    
    return {
        "blog_plan": response.model_dump(), # Convert Pydantic object to dictionary
        "tasks": response.tasks,       # Extract tasks for the next node
        "messages": [ai_msg],          # Append to the message history
        "human_feedback":"awaiting",
        "interrupt_type":"plan_review"
    }

if __name__ == "__main__":
    # Test execution
    state = BlogAgentState(
        prompt="Write a blog post about the latest trends in MLOps for 2026.",
        research_summary="In 2026, MLOps has evolved to include automated model monitoring, real-time data drift detection, and seamless integration with edge devices."
    )

    plan = planner_node(state)

    print(plan)
