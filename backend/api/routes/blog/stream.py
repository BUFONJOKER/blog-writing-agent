from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json

router = APIRouter()


# -------------------------
# SSE STREAM
# -------------------------
@router.get("/stream/{thread_id}")
async def stream_blog(thread_id: str, request: Request):
    """Stream workflow events to the client as server-sent events.

    Args:
        thread_id: Unique identifier for the workflow thread to consume.
        request: FastAPI request used to access the shared stream manager.

    Returns:
        StreamingResponse: SSE response that yields queued workflow events.
    """
    stream_manager = request.app.state.stream_manager
    queue = stream_manager.get_queue(thread_id)

    async def sse_generator():
        """Yield queued stream events until the terminal event is received.

        Args:
            None: The generator reads from the thread-specific queue directly.

        Returns:
            AsyncIterator[str]: SSE-formatted event payloads for the client.
        """
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
