from pydantic import BaseModel, Field

class FinalPostRequest(BaseModel):
    """Payload for retrieving the final blog post for a specific workflow run.

    Args:
        user_id: User identifier used for ownership verification.
        thread_id: Workflow thread identifier for the generated blog run.

    Returns:
        FinalPostRequest: A validated request model instance.
    """

    user_id: str = Field(..., example="user123")
    thread_id: str = Field(..., example="thread123")