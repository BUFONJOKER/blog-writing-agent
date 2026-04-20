from fastapi import APIRouter, Request, HTTPException
from db.crud.blog_outputs import get_output
from api.schema.blog_states import FinalPostRequest

router = APIRouter()


# -------------------------
# FINAL POST
# -------------------------
@router.post("/final_post")
async def get_final_post(payload: FinalPostRequest, request: Request):
    """Return the finalized blog output for the requesting user.

    Args:
        payload: Request body containing the user id and workflow thread id.
        request: FastAPI request used to access the database pool.

    Returns:
        dict: The stored final post output if the user owns the run.

    Raises:
        HTTPException: If no matching final post is found for the user.
    """
    pool = request.app.state.resources.pool

    output = await get_output(pool, payload.thread_id)

    if output and output["user_id"] == payload.user_id:
        return output

    raise HTTPException(status_code=404, detail="Final post not found.")
