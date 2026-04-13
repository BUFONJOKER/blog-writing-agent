from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json

router = APIRouter()

# -------------------------
# SSE STREAM
# -------------------------
@router.get("/stream/{thread_id}")
async def stream_blog(thread_id: str, request: Request):
    stream_manager = request.app.state.stream_manager
    queue = stream_manager.get_queue(thread_id)

    async def sse_generator():
        while True:
            event = await queue.get()

            yield f"data: {json.dumps(event)}\n\n"

            if event.get("event") == "stream_end":
                break

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )