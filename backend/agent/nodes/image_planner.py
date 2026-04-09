from agent.state import BlogAgentState
from pydantic import BaseModel, Field
from typing_extensions import List
from langchain_core.prompts import ChatPromptTemplate


class ImagePlacement(BaseModel):
    prompt: str = Field(
        description="Highly detailed visual description for the image generator."
    )
    after_section: str = Field(
        description="The exact header text of the blog post after which the image should be placed."
    )


class ImagePlannerInput(BaseModel):
    image_plan: List[ImagePlacement]


def image_planner_node(state: BlogAgentState, model) -> dict:

    # model = load_model()

    structured_model = model.with_structured_output(
        schema=ImagePlannerInput, method="function_calling"
    )

    system_prompt = """
    You are a senior visual content strategist and image planner for high-quality blog posts.

    Your task is to analyze the given blog post and generate a precise, structured image placement plan.

    ## Objectives
    - Improve reader engagement
    - Enhance clarity of complex ideas
    - Break long text sections visually
    - Align visuals with section meaning (not random decoration)

    ## Rules for Image Placement
    1. Place images ONLY after meaningful sections (not after every section).
    2. Prefer sections that:
    - Introduce new concepts
    - Contain technical explanations
    - Include comparisons, workflows, or step-by-step processes
    3. Avoid placing images after:
    - Conclusion sections
    - Very short sections
    4. Use the EXACT section header text as written in the blog.

    ## Image Prompt Requirements
    Each image prompt MUST:
    - Be highly detailed and descriptive (minimum 30-60 words)
    - Be written for AI image generation (like Midjourney / DALL·E)
    - Include:
    - Main subject
    - Scene/environment
    - Style (e.g., realistic, 3D render, isometric, illustration)
    - Lighting and mood
    - Camera angle or composition (if relevant)
    - Be specific to the section content (no generic images)

    ## Do NOT:
    - Do NOT repeat similar prompts
    - Do NOT generate vague descriptions like "an image showing technology"
    - Do NOT invent section names (must match exactly)

    ## Output Format
    Return ONLY structured data following the schema:
    - prompt: detailed image generation prompt
    - after_section: exact section header

    ## Example
    Input Section:
    "## How Neural Networks Work"

    Output:
    {{
    "prompt": "A detailed 3D visualization of a neural network with multiple interconnected layers, glowing nodes and flowing data connections, futuristic digital environment, soft blue lighting, isometric perspective, high detail, modern AI concept art",
    "after_section": "## How Neural Networks Work"
    }}

    Generate 3-6 high-quality image placements depending on blog length.
    """

    user_prompt = """
    Analyze the following blog post and create a high-quality image placement plan.

    ## Blog Post:
    {blog_post}

    ## Instructions:
    - Carefully read the full blog
    - Identify the most important sections where visuals will add value
    - Generate 3-6 image placements (not too many, not too few)
    - Ensure each image is unique and tailored to its section

    Return only structured output.
    """

    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", user_prompt)]
    )

    chain = prompt | structured_model

    input_variables = {"blog_post": state.final_post}

    response = chain.invoke(input_variables)

    return {"image_plan": [item.model_dump() for item in response.image_plan]}