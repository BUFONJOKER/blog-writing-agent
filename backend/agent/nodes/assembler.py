from pydantic import BaseModel, Field, field_validator
from typing import List
from agent.state import BlogAgentState
from langchain_core.prompts import ChatPromptTemplate

# --- 1. Define Pydantic Models ---


class BlogDraft(BaseModel):
    """Structured assembled blog draft produced by the assembler node."""

    title: str = Field(..., description="The main H1 title of the blog post.")
    meta_description: str = Field(
        ..., description="A compelling summary for SEO search results (120-160 chars)."
    )
    content: str = Field(..., description="The full markdown body of the blog.")
    keywords_used: List[str] = Field(
        default_factory=list, description="List of SEO keywords included in the text."
    )
    slug: str = Field(..., description="The URL-friendly version of the title.")


# --- 2. Updated Assembler Node ---


def assembler_node(state: BlogAgentState, model) -> dict:
    """Combine drafted sections into a structured blog draft.

    Args:
        state: Current workflow state containing the blog plan and section output.
        model: Language model used to generate the structured draft.

    Returns:
        dict: Assembled draft content and metadata for downstream editing.
    """
    # Load model and bind the Pydantic schema for structured output
    if state.edited_draft:
        return {"edited_draft": state.edited_draft}

    base_model = model
    structured_model = base_model.with_structured_output(
        schema=BlogDraft, method="function_calling"
    )

    blog_plan = state.blog_plan
    blog_title = blog_plan["title"]
    blog_subtitle = blog_plan["subtitle"]
    blog_sections = blog_plan["sections"]
    tasks_output = state.tasks_output

    # Dynamically build raw blog draft for the LLM to refine
    sections_block = ""
    all_keywords = []

    for i, section in enumerate(blog_sections):
        section_name = section["name"]
        section_content = tasks_output.get(section_name, "Content not available.")
        keywords = section.get("seo_keywords", [])
        all_keywords.extend(keywords)

        sections_block += f"""
    ### Section {i+1}: {section_name}
    {section_content}
    """

    system_prompt = """
    You are an expert Content Strategist and SEO Editor. Your task is to assemble fragmented section drafts into a premium, publication-ready blog post.

    CRITICAL OUTPUT CONSTRAINTS:
    1. SCHEMA ADHERENCE: You must return a structured response matching the 'BlogDraft' schema exactly.
    2. COHESION: Erase repetitive phrasing between sections and create seamless narrative transitions.
    3. SEO INTEGRATION: Naturally weave primary keywords into headings (H1, H2) and the first 100 words of the content.
    4. FORMATTING: Use clean Markdown. Ensure a logical hierarchy (H1 > H2 > H3).
    5. META DATA:
    - Meta Description MUST be between 120 and 150 characters.
    - CRITICAL: Do NOT exceed 160 characters under any circumstances.
    """

    user_prompt = """
    I have a raw collection of blog sections and a target keyword list.

    RAW CONTENT:
    Blog Title: {blog_title}
    Blog Subtitle: {blog_subtitle}
    Sections: {sections_block}

    TARGET SEO KEYWORDS:
    {all_keywords}

    EDITORIAL REQUIREMENTS:
    - TITLE: Craft a compelling H1 if the current one is weak.
    - TONE: Maintain a professional yet accessible 'Technical Educator' voice.
    - REFINEMENT: Remove any 'Section X' markers or internal drafting notes.
    - VALIDATION: Ensure the 'meta_description' is concise and the 'slug' is URL-safe.

    Generate the final polished BlogDraft object now.
    """

    chat_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )

    chain = chat_prompt | structured_model

    input_variables = {
        "blog_title": blog_title,
        "blog_subtitle": blog_subtitle,
        "all_keywords": all_keywords,
        "sections_block": sections_block,
    }

    final_output: BlogDraft = chain.invoke(input_variables)

    return {
        "draft": final_output.content,
        "meta_description": final_output.meta_description,
        "slug": final_output.slug,
        "keywords_used": final_output.keywords_used,
        "title": final_output.title,
    }
