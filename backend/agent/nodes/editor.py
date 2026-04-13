from agent.state import BlogAgentState
from langchain_core.prompts import ChatPromptTemplate


def editor_node(state: BlogAgentState, model) -> dict:
    """Perform a final editorial pass on the assembled blog draft.

    Args:
        state: Current workflow state containing the assembled draft.
        model: Language model used to refine the draft.

    Returns:
        dict: The fully edited draft ready for critic review or finalization.
    """

    # model = load_model()

    draft = state.draft

    if state.edited_draft:
        draft = state.edited_draft

    system_prompt = """
    You are an expert **Editor Node** in a blog generation pipeline. Your role is to perform a **final-pass edit** on an already assembled draft. You must **refine and improve the existing content**, not generate new content or alter its core meaning.

    ### Objectives:

    * Ensure the blog reads as a **single, coherent, and polished article**
    * Improve **clarity, flow, and readability** without changing factual substance

    ### Responsibilities:

    1. **Structure & Organization**

    * Normalize and standardize markdown headings (H1, H2, H3)
    * Ensure logical flow between sections
    * Improve overall article structure where needed

    2. **Language & Style**

    * Fix grammar, punctuation, and spelling errors
    * Improve sentence clarity and conciseness
    * Maintain a consistent tone and style throughout

    3. **Transitions & Coherence**

    * Smooth transitions between paragraphs and sections
    * Eliminate abrupt or disjointed shifts in ideas

    4. **Redundancy Removal**

    * Remove repetitive or duplicated information
    * Consolidate overlapping points

    5. **Light SEO Optimization**

    * Ensure keywords are used naturally (no keyword stuffing)
    * Align title, subtitle, and body content for consistency

    ### Constraints:

    *  Do NOT introduce new facts, claims, or sections
    *  Do NOT significantly rewrite or expand content
    *  Do NOT change the original intent or meaning

    ### Output:

    Return the **fully edited, clean, and polished blog draft** in proper markdown format, ready for publishing."
    """

    user_prompt = """
    Here’s a **clean and aligned User Prompt** for your Editor Node:

    ---

    **User Prompt: Editor Node**

    "Refine the following assembled blog draft by performing a final-pass edit.

    Focus on:

    * Improving clarity, grammar, and readability
    * Ensuring smooth transitions between sections
    * Removing repetition and redundant content
    * Normalizing markdown structure (headings, formatting)
    * Making the article flow as a single, coherent piece
    * Applying light SEO improvements (natural keyword usage and alignment between title, subtitle, and body)

    Do not add new information, change the meaning, or introduce new sections.

    ### Blog Draft:

    {draft}

    ### Output:

    Return the fully edited and polished blog in clean markdown format, ready for publishing."
    """

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", user_prompt)]
    )

    chain = prompt_template | model

    input_variables = {"draft": draft}

    response = chain.invoke(input_variables)

    edited_draft = response.content

    return {"edited_draft": edited_draft}
