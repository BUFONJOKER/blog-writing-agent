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
