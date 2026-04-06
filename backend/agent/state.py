from pydantic import BaseModel, Field
from typing import Annotated, Literal, List, Any
from langgraph.graph.message import AnyMessage, add_messages
import operator


class BlogAgentState(BaseModel):
    """Shared runtime state passed between all nodes in the blog-writing graph."""

    # 1. The only mandatory field
    prompt: str = Field(description="Original user request for the blog post.")

    # --- All other fields now have defaults ---

    topic: str = Field(
        default="", description="The main topic or subject of the user's prompt."
    )

    needs_research: bool = Field(
        default=False, description="Routing decision for external research."
    )

    research_queries: List[str] = Field(
        default_factory=list, description="Search queries generated from the prompt."
    )

    research_results: Annotated[List[dict], operator.add] = Field(
        default_factory=list, description="Accumulated results from research tools."
    )

    research_summary: str = Field(
        default="", description="Condensed synthesis of the collected research."
    )

    blog_plan: dict = Field(
        default_factory=dict, description="Structured outline for the article."
    )

    tasks: List[str] = Field(
        default_factory=list, description="Section-level writing tasks."
    )

    tasks_output: Annotated[dict, operator.or_] = Field(
        default_factory=dict, description="Merged dictionary of task results."
    )

    draft: str = Field(default="", description="First complete markdown draft.")

    final_post: str = Field(default="", description="Final edited article.")

    human_feedback: str | None = Field(
        default=None, description="Optional reviewer feedback."
    )

    iteration_count: int = Field(
        default=0, ge=0, le=3, description="Number of revision cycles."
    )

    thread_id: str = Field(default="", description="Unique identifier for the run.")

    status: str = Field(
        default="running", description="Current lifecycle state of the run."
    )

    interrupt_type: str | None = Field(
        default=None, description="Checkpoint type when paused."
    )

    error: str | None = Field(default=None, description="Optional error details.")

    metadata: dict = Field(
        default_factory=dict, description="Supplementary generation preferences."
    )

    needs_revision: bool = Field(
        default=False, description="Determines if another revision cycle is needed."
    )

    feedback: dict = Field(
        default_factory=dict, description="Structured feedback from critic node."
    )

    more_research_needed: bool = Field(
        default=False, description="Indicates if additional research is required."
    )

    research_gaps: List[str] = Field(
        default_factory=list, description="List of missing topics."
    )

    current_task: str | None = Field(
        default=None, description="Currently executing task."
    )

    agent_thoughts: List[str] = Field(
        default_factory=list, description="Chain-of-thought style reasoning summaries."
    )

    confidence_score: float = Field(
        default=1.0, ge=0, le=1, description="Confidence level of the final output."
    )

    tool_call_count: Annotated[int, operator.add] = Field(
        default=0, ge=0, description="Cumulative count of tool invocations."
    )

    max_tool_calls: int = Field(
        default=20, ge=1, description="Hard cap for tool calls."
    )

    messages: Annotated[list[AnyMessage], add_messages] = Field(
        default_factory=list,
        description="Chronological list of all messages exchanged with the LLM.",
    )

    has_tool_calls: bool = Field(
        default=False,
        description="Flag indicating if the last LLM response contained tool calls.",
    )

    meta_description: str = Field(
        default="",
        min_length=120,
        max_length=160,
        description="A compelling summary for SEO search results (120-160 chars).",
    )

    keywords_used: List[str] = Field(
        default_factory=list, description="List of SEO keywords included in the text."
    )

    slug: str = Field(default="", description="The URL-friendly version of the title.")

    title: str = Field(default="", description="The main H1 title of the blog post.")

    edited_draft: str = Field(
        default="",
        description="The final edited version of the draft after passing through the Editor Node.",
    )

    critic_feedback: dict = Field(
        default_factory=dict,
        description="Structured feedback from the Critic Node, including issues and suggestions for improvement.",
    )

    quality_score: int = Field(
        default=10,
        ge=1,
        le=10,
        description="Overall quality score (1-10).",
    )

    revision_cycles: int = Field(
        default=0,
        description="Number of times the content has been revised based on critic feedback.",
    )
