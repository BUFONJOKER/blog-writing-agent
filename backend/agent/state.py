from pydantic import BaseModel, Field
from typing import Annotated, Literal, List
import operator

class BlogAgentState(BaseModel):
    """Shared runtime state passed between all nodes in the blog-writing graph.

    Each field represents a piece of data produced or consumed by one or more
    nodes (routing, research, planning, drafting, review, and finalization).
    Keeping this schema explicit makes node behavior predictable and easier to
    validate, debug, and evolve.
    """

    prompt: Annotated[
        str,
        Field(description="Original user request for the blog post. This value should remain unchanged for the entire run.")
    ]

    needs_research: Annotated[
        Literal[True, False],
        Field(description="Routing decision that determines whether external research must run before planning and writing."),
    ] = False  # Default to False, but the router node will set this based on the prompt analysis

    research_queries: Annotated[
        List[str],
        Field(description="Search queries generated from the prompt to collect source material and factual context.")
    ] = Field(default_factory=list)  # Start with an empty list, to be populated by the research node

    research_results: Annotated[
        List[dict],
        Field(description="Raw outputs returned by research tools (search and page fetch), preserved for traceability before summarization.")
    ] = Field(default_factory=list)

    research_summary: Annotated[
        str,
        Field(description="Condensed synthesis of the collected research used as grounded context for planning and drafting.")
    ] = Field(default_factory=str)

    blog_plan: Annotated[
        dict,
        Field(description="Structured outline for the article, typically including title, section breakdown, tone, and target audience.")
    ] = Field(default_factory=dict)

    tasks: Annotated[
        List[str],
        Field(description="Section-level writing tasks derived from the plan; each item represents one unit of writing work.")
    ] = Field(default_factory=list)

    task_outputs: Annotated[
        dict,
        operator.or_,
    ] = Field(
        default_factory=dict,
        description="This allows multiple nodes to add their specific task results and merge them into one dictionary.",
    )

    draft: Annotated[
        str,
        Field(description="First complete markdown draft assembled from all section outputs.")
    ] = Field(default_factory=str)

    final_post: Annotated[
        str,
        Field(description="Final edited article after revision, polishing, and any human-in-the-loop adjustments.")
    ] = Field(default_factory=str)

    human_feedback: Annotated[
        str|None,
        Field(description="Optional reviewer feedback captured at checkpoints and used to guide re-planning or revision.")
    ] = None

    iteration_count: Annotated[
        int,
        Field(ge=0, le=3, description="Number of revision cycles completed so far; constrained to 0-3 to prevent unbounded loops.")
    ] = 0

    thread_id: Annotated[
        str,
        Field(description="Run-level unique identifier used to correlate state, logs, events, and API calls for this execution.")
    ] = Field(default_factory=str)

    status: Annotated[
        str,
        Field(description="Current lifecycle state of the run (for example: running, awaiting_human, complete, or error).")
    ] = Field(default=str)

    interrupt_type: Annotated[
        str|None,
        Field(description="Checkpoint type when paused for review, such as plan_review or final_review.")
    ] = None

    error: Annotated[
        str|None,
        Field(description="Optional error details when execution fails, intended for debugging, observability, and client reporting.")
    ] = None

    metadata: Annotated[
        dict,
        Field(description="Supplementary generation preferences and constraints, such as tone, audience, word target, and SEO keywords.")
    ] = Field(default_factory=dict)