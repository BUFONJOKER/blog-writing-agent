from fastapi import APIRouter, Request, HTTPException
from backend.db.crud.blog_runs import get_run

router = APIRouter()


# -------------------------
# STATUS
# -------------------------
@router.get("/status/{thread_id}")
async def check_blog_status(thread_id: str, request: Request):
    pool = request.app.state.resources.pool

    run_data = await get_run(pool, thread_id)

    if not run_data:
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "status": run_data["status"],
        "is_waiting_for_you": run_data["status"] == "waiting_approval",
        "error": run_data["error_message"],
    }
