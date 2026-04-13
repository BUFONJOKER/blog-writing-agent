from agent.state import BlogAgentState
from langchain_core.prompts import ChatPromptTemplate


def finalize_node(state: BlogAgentState, model) -> dict:
    """Finalize the blog post by refining the draft.

    Args:
        state: Current graph state containing the draft
        A partial state dictionary with the finalized blog content ready for publication.
    Return:
        cleaned, formatted final blog post
    """
    # model = load_model()

    edited_draft = state.edited_draft

    system_prompt = """
    You are a senior editorial blog finisher. Your job is to transform the provided draft \n {draft} into a publish-ready blog post.

    You must:
    - Preserve the core meaning, facts, and structure of the draft
    - Improve flow, transitions, readability, and formatting
    - Remove repetition, awkward phrasing, and weak conclusions
    - Ensure the final output is clean, coherent, and ready to publish in Markdown

    You must not:
    - Introduce new major ideas or unsupported facts
    - Add commentary about your process
    - Mention that you are editing or finalizing
    - Output anything except the final blog content

    Priorities:
    - Clarity first
    - Accuracy second
    - Readability third
    - Formatting polish last
    """

    user_prompt = """
    Finalize the blog post using the provided draft.

    Make the article feel complete and publication-ready by:
    - Fixing any structural issues
    - Strengthening transitions between sections
    - Improving the introduction and conclusion
    - Removing duplication and filler
    - Aligning the tone with the target audience
    - Applying final Markdown cleanup

    Return only the final Markdown version of the blog post.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", user_prompt),
        ]
    )

    chain = prompt | model

    input_variables = {"draft": edited_draft}

    response = chain.invoke(input_variables)

    final_post = response.content

    return {"final_post": final_post}
    