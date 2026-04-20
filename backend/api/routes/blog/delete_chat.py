from fastapi import APIRouter, Request, HTTPException
from db.crud.blog_runs import delete_blog_run
from api.schema.blog_states import DeleteThreadRequest

router = APIRouter()


# -------------------------
# DELETE THREAD
# -------------------------
@router.delete("/delete_thread")
async def delete_thread(payload: DeleteThreadRequest, request: Request):
    """Delete a blog run thread from the database.

    Args:
        payload: Request body containing the user id and thread id.
        request: FastAPI request used to access the database pool.

    Returns:
        dict: A confirmation message if deletion was successful.

    Raises:
        HTTPException: If the thread doesn't belong to the user or doesn't exist.
    """
    pool = request.app.state.resources.pool

    success = await delete_blog_run(pool, payload.thread_id, payload.user_id)

    if not success:
        raise HTTPException(status_code=403, detail="Thread could not be deleted.")

    return {"message": "Thread deleted successfully", "thread_id": payload.thread_id}
