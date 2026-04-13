from fastapi import APIRouter, Request, HTTPException
import asyncio
import uuid
from api.schema.blog_states import BlogRequest
from agent.main import agent

router = APIRouter()


@router.post("/generate")
async def generate_blog(payload: BlogRequest, request: Request):
    """Start a new blog generation workflow and return the stream URL.

    Args:
        payload: Blog generation request containing the user id and prompt.
        request: FastAPI request used to access shared application resources.

    Returns:
        dict: Queue metadata including the workflow thread id and stream URL.

    Raises:
        HTTPException: If the workflow cannot be queued.
    """
    try:
        thread_id = str(uuid.uuid4())
        resources = request.app.state.resources
        stream_manager = request.app.state.stream_manager

        run_name = f"Blog Run - {payload.prompt[:30]}..."

        asyncio.create_task(
            agent(
                workflow=resources.workflow,
                pool=resources.pool,
                stream_manager=stream_manager,
                user_id=payload.user_id,
                thread_id=thread_id,
                prompt=payload.prompt,
                run_name=run_name,
            )
        )

        return {
            "user_id": payload.user_id,
            "thread_id": thread_id,
            "status": "queued",
            "stream_url": str(request.url.replace(path=f"/blog/stream/{thread_id}")),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
