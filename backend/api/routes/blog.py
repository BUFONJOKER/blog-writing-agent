from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
import asyncio
import uuid
import json
from fastapi.responses import StreamingResponse
from db.crud.blog_runs import create_blog_run, update_run_status, utc_now, get_run
from db.crud.blog_outputs import get_output, get_all_outputs_of_user, save_output
from langgraph.types import Command
from api.schema.blog.states import BlogRequest, ReviewRequest, FinalPostRequest
from agent.main import agent, finalize_workflow
from typing import Any

blog_router = APIRouter(prefix="/blog", tags=["Blog Generation"])




@blog_router.post("/generate")
async def generate_blog(payload: BlogRequest, request: Request):
    """Start blog generation in BACKGROUND and return SSE stream URL instantly."""
    try:
        thread_id = str(uuid.uuid4())
        resources = request.app.state.resources
        resources.prompt = payload.prompt  # For stream/review use
        run_name = f"Blog Run - {payload.prompt[:30]}..."
        resources.run_name = run_name  # For stream/review use

        # START BACKGROUND AGENT - NON-BLOCKING!
        asyncio.create_task(
            agent(
                workflow=resources.workflow,
                pool=resources.pool,
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
            "stream_url": str(request.url.replace(path=f"/stream/{thread_id}"))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue: {str(e)}")

def to_json_serializable(obj: Any) -> Any:
    """Recursively convert Pydantic models and non-JSON types to JSON-safe."""
    if isinstance(obj, BaseModel):
        return to_json_serializable(obj.model_dump())  # Pydantic v2: model_dump()
    elif isinstance(obj, dict):
        return {k: to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_json_serializable(v) for v in obj]
    elif hasattr(obj, '__dict__'):  # Custom objects
        return to_json_serializable(obj.__dict__)
    elif obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    else:
        return str(obj)  # Fallback: convert to string


@blog_router.get("/stream/{thread_id}")
async def stream_blog(thread_id: str, request: Request):
    resources = request.app.state.resources
    prompt = resources.prompt  # Get the prompt set at generation time, if needed for context in streaming
    config = {
        "configurable": {"thread_id": thread_id},
        "run_name": getattr(resources, 'run_name', 'Blog Run')
    }

    async def sse_generator():
        try:
            async for event in resources.workflow.astream_events(
                {'prompt': prompt}, config, version="v2",
                stream_mode=["updates", "messages"]
            ):
                # SERIALIZE BEFORE JSON!
                safe_event = to_json_serializable(event)
                yield f"data: {json.dumps(safe_event)}\n\n"
            yield 'data: {"event": "stream_end", "message": "Workflow complete"}\n\n'
        except Exception as e:
            yield f'data: {{"error": "{str(e)}"}}\n\n'

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )


@blog_router.post("/review")
async def review_blog(payload: ReviewRequest, request: Request):
    """Process human review - resume workflow."""
    resources = request.app.state.resources
    config = {"configurable": {"thread_id": payload.thread_id}, "run_name": resources.run_name}

    await update_run_status(pool=resources.pool, thread_id=payload.thread_id, status="running")

    try:
        async for event in resources.workflow.astream(
            Command(resume=payload.approved), config, stream_mode="values"
        ):
            pass

        asyncio.create_task(
            finalize_workflow(resources.workflow, config, resources.pool, payload.thread_id)
        )
        return {"message": "Review processed. Check stream for updates."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Review failed: {str(e)}")



@blog_router.post("/final_post")
async def get_final_post(payload: FinalPostRequest, request: Request):
    """Return the final blog output if it belongs to the requesting user.

    Args:
        payload: Request body containing user id and workflow thread id.
        request: FastAPI request object used to access the database pool.

    Returns:
        dict: Final blog markdown and metadata for the requested thread.

    Raises:
        HTTPException: If no matching output is found for user and thread id.
    """

    pool = request.app.state.resources.pool
    output = await get_output(pool, payload.thread_id)

    # Check if output exists AND belongs to the user entered
    if output and output["user_id"] == payload.user_id:
        return {
            "thread_id": payload.thread_id,
            "user_id": payload.user_id,
            "final_post_markdown": output["final_post_markdown"],
            "meta": output["meta"],
            "created_at": output["created_at"],
        }
    else:
        raise HTTPException(
            status_code=404,
            detail="Final post not found for the given thread_id and user_id.",
        )

@blog_router.get("/user_posts/{user_id}")
async def get_user_posts(user_id: str, request: Request):
    """Fetch all blog posts generated by a specific user.

    Args:
        user_id: Identifier for the user whose posts to retrieve.
        request: FastAPI request object used to access the database pool.

    Returns:
        list: A list of blog posts associated with the user.

    Raises:
        HTTPException: If no posts are found for the given user.
    """

    pool = request.app.state.resources.pool

    posts = await get_all_outputs_of_user(pool, user_id)

    if not posts:
        raise HTTPException(
            status_code=404,
            detail="No blog posts found for the given user.",
        )

    return posts

# --- routers/blog.py ---


@blog_router.get("/status/{thread_id}")
async def check_blog_status(thread_id: str, request: Request):
    """Fetch the execution status of a blog generation run.

    Args:
        thread_id: Workflow thread identifier to inspect.
        request: FastAPI request object used to access the database pool.

    Returns:
        dict: Status payload including current state, wait flag, and error.

    Raises:
        HTTPException: If the specified blog run does not exist.
    """

    pool = request.app.state.resources.pool

    # Use the function you just showed me
    run_data = await get_run(pool, thread_id)

    if not run_data:
        raise HTTPException(status_code=404, detail="Blog run not found")

    return {
        "status": run_data["status"],
        "is_waiting_for_you": run_data["status"] == "waiting_approval",
        "error": run_data["error_message"],
    }
