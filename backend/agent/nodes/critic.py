import json
from typing import List

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, field_validator

from agent.state import BlogAgentState


class Feedback(BaseModel):
    issues: List[str] = Field(
        ..., description="List of identified issues in the blog draft."
    )
    suggestions: List[str] = Field(
        ..., description="Actionable suggestions to fix the issues."
    )


class CriticFeedback(BaseModel):
    feedback: Feedback = Field(
        ..., description="Structured feedback containing issues and suggestions."
    )

    @field_validator("feedback", mode="before")
    @classmethod
    def coerce_feedback(cls, value):
        # Some models return nested objects as JSON strings; normalize before validation.
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError as exc:
                raise ValueError("feedback must be a valid JSON object string") from exc
            return parsed
        return value

    needs_revision: bool = Field(
        ...,
        description="needs_revision will be True if the draft has critical issues that require a revision cycle and False if the draft is of sufficient quality to proceed without changes.",
    )

    quality_score: int = Field(
        ...,
        ge=1,
        le=10,
        description="Overall quality score (1-10).",
    )

    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0-1.0).",
    )


def critic_node(state: BlogAgentState, model) -> dict:

    # model = load_model()
    structured_model = model.with_structured_output(
        schema=CriticFeedback, method="function_calling"
    )

    edited_draft = state.edited_draft
    keywords_used = state.keywords_used
    system_prompt = """
    You are a Senior Technical Editor and SEO Critic. Your role is to evaluate blog drafts for technical accuracy, narrative flow, and SEO optimization.

    EVALUATION CRITERIA:
    1. TECHNICAL ACCURACY: Does the content reflect current 2026 standards?
    2. SEO VIGILANCE: Are keywords integrated naturally without "stuffing"?
    3. READABILITY: Is the Markdown hierarchy logical and the tone consistent?

    OUTPUT INSTRUCTIONS:
    - You must return a structured response matching the provided schema.
    - 'feedback.issues': MUST be a list of plain strings (no objects, no dictionaries)
    - 'feedback.suggestions': MUST be a list of plain strings
    - Do NOT return structured objects like {{description, severity}}
    - 'issues': Identify specific technical or stylistic errors.
    - 'suggestions': Provide clear, actionable steps to fix each identified issue.
    - 'needs_revision': Set to True only if critical errors or SEO gaps exist.
    - 'quality_score': Rate 1-10 (10 being publication-ready).
    - 'confidence_score': Rate 0.0-1.0 based on your certainty of the feedback.
    """

    user_prompt = """
    Review the following blog draft and provide a structured critique.

    BLOG DRAFT:
    {edited_draft}

    TARGET KEYWORDS:
    {keywords}

    TASK:
    1. Analyze the draft for clarity, keyword placement, and engagement.
    2. Identify any obsolete terminology (e.g., ensure "MCP servers" are correctly debunked).
    3. Determine if the draft requires a revision cycle.

    Generate the critique object now.
    """

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", user_prompt)]
    )

    chain = prompt_template | structured_model

    input_variables = {
        "edited_draft": edited_draft,
        "keywords": list(set(keywords_used)),
    }

    response = chain.invoke(input_variables)

    return {
        "critic_feedback": response.feedback.model_dump(),
        "needs_revision": response.needs_revision,
        "quality_score": response.quality_score,
        "confidence_score": response.confidence_score,
    }