from fastapi import APIRouter, Request, HTTPException
from db.crud.blog_outputs import get_all_outputs_of_user

router = APIRouter()


# -------------------------
# USER POSTS
# -------------------------
@router.get("/user_posts/{user_id}")
async def get_user_posts(user_id: str, request: Request):
    """Return all finalized blog outputs associated with a user.

    Args:
        user_id: Identifier for the user whose posts should be returned.
        request: FastAPI request used to access the database pool.

    Returns:
        list: Finalized blog outputs ordered from newest to oldest.

    Raises:
        HTTPException: If the user has no blog posts.
    """
    pool = request.app.state.resources.pool

    posts = await get_all_outputs_of_user(pool, user_id)

    if not posts:
        raise HTTPException(status_code=404, detail="No posts found")

    return posts
