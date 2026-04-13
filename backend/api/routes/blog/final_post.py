from fastapi import APIRouter, Request, HTTPException
from db.crud.blog_outputs import get_output
from api.schema.blog_states import FinalPostRequest

router = APIRouter()

# -------------------------
# FINAL POST
# -------------------------
@router.post("/final_post")
async def get_final_post(payload: FinalPostRequest, request: Request):
    pool = request.app.state.resources.pool

    output = await get_output(pool, payload.thread_id)

    if output and output["user_id"] == payload.user_id:
        return output

    raise HTTPException(status_code=404, detail="Not found")