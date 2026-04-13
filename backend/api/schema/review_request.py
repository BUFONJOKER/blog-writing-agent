from pydantic import BaseModel, Field

# schema for review request payload for the /review endpoint
class ReviewRequest(BaseModel):
    """Payload for approving or rejecting a workflow at human-review step.

    Args:
        thread_id: Workflow thread identifier to resume.
        approved: Review decision. `True` continues workflow, `False` rejects.

    Returns:
        ReviewRequest: A validated request model instance.
    """

    thread_id: str = Field(..., example="thread123")
    approved: bool = Field(..., example=True)