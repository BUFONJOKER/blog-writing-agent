from pydantic import BaseModel, Field


# schema for blog generation request payload for the /generate endpoint
class BlogRequest(BaseModel):
    """Payload for starting a new blog generation workflow.

    Args:
        user_id: Unique identifier for the user requesting blog generation.
        prompt: Natural language topic/instruction used to generate the blog.

    Returns:
        BlogRequest: A validated request model instance.
    """

    user_id: str = Field(..., example="user123")
    prompt: str = Field(
        ..., example="Write a blog about the benefits of AI for small businesses."
    )


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


class DeleteThreadRequest(BaseModel):
    """Payload for deleting a blog run thread.

    Args:
        user_id: User identifier for ownership verification.
        thread_id: Workflow thread identifier to delete.

    Returns:
        DeleteThreadRequest: A validated request model instance.
    """

    user_id: str = Field(..., example="user123")
    thread_id: str = Field(..., example="thread123")
