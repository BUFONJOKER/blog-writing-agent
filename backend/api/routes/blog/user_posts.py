from fastapi import APIRouter, Request, HTTPException
from db.crud.blog_outputs import get_all_outputs_of_user

router = APIRouter()

# -------------------------
# USER POSTS
# -------------------------
@router.get("/user_posts/{user_id}")
async def get_user_posts(user_id: str, request: Request):
    pool = request.app.state.resources.pool

    posts = await get_all_outputs_of_user(pool, user_id)

    if not posts:
        raise HTTPException(status_code=404, detail="No posts found")

    return posts