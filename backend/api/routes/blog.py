from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
import uuid
import json

from langgraph.types import Command

from backend.db.crud.blog_runs import update_run_status, get_run
from backend.db.crud.blog_outputs import get_output, get_all_outputs_of_user

from api.schema.blog_states import BlogRequest, ReviewRequest, FinalPostRequest
from agent.main import agent, finalize_workflow

from api.routes.blog import blog_router


# -------------------------
# GENERATE BLOG
# -------------------------
@blog_router.post("/generate")
async def generate_blog(payload: BlogRequest, request: Request):
    """Start a new blog generation workflow and return its stream URL.

    Args:
        payload: Blog request containing the user id and prompt.
        request: FastAPI request used to access shared application resources.

    Returns:
        dict: Queue metadata including the thread id and SSE stream URL.

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


# -------------------------
# SSE STREAM
# -------------------------
@blog_router.get("/stream/{thread_id}")
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


# -------------------------
# REVIEW
# -------------------------
@blog_router.post("/review")
async def review_blog(payload: ReviewRequest, request: Request):
    """Resume a paused workflow after human review is submitted.

    Args:
        payload: Review payload containing the thread id and approval flag.
        request: FastAPI request used to access shared application resources.

    Returns:
        dict: A confirmation message when review processing is accepted.

    Raises:
        HTTPException: If the run cannot be resumed or review processing fails.
    """
    resources = request.app.state.resources
    stream_manager = request.app.state.stream_manager

    config = {
        "configurable": {"thread_id": payload.thread_id},
        "run_name": "Review Run",
    }

    run_data = await get_run(resources.pool, payload.thread_id)
    if not run_data:
        raise HTTPException(status_code=404, detail="Run not found")

    if run_data["status"] != "waiting_approval":
        raise HTTPException(
            status_code=409,
            detail=f"Run is not awaiting review (current status: {run_data['status']})",
        )

    graph_state = await resources.workflow.aget_state(config)
    if not graph_state.next or "human_review" not in graph_state.next:
        raise HTTPException(
            status_code=409,
            detail="No resumable human review checkpoint found for this thread",
        )

    await update_run_status(
        pool=resources.pool,
        thread_id=payload.thread_id,
        status="running",
    )

    try:
        async for event in resources.workflow.astream(
            Command(resume=payload.approved),
            config,
            stream_mode="updates",
        ):
            await stream_manager.publish(
                payload.thread_id,
                {
                    "type": "update",
                    "data": event,
                },
            )

        async def _finalize_with_guard():
            """Finalize the resumed workflow and close the stream on failure.

            Args:
                None: The helper captures the enclosing review context directly.

            Returns:
                None: Finalization is performed asynchronously as a background task.
            """
            try:
                await finalize_workflow(
                    workflow=resources.workflow,
                    config=config,
                    pool=resources.pool,
                    thread_id=payload.thread_id,
                    stream_manager=stream_manager,
                )
            except Exception as e:
                await update_run_status(
                    pool=resources.pool,
                    thread_id=payload.thread_id,
                    status="failed",
                    error_message=str(e),
                    interrupt_type="error",
                )
                await stream_manager.publish(
                    payload.thread_id,
                    {
                        "type": "error",
                        "message": str(e),
                    },
                )
                await stream_manager.close(payload.thread_id)

        asyncio.create_task(_finalize_with_guard())

        return {"message": "Review processed"}

    except Exception as e:
        await update_run_status(
            pool=resources.pool,
            thread_id=payload.thread_id,
            status="failed",
            error_message=str(e),
            interrupt_type="error",
        )
        await stream_manager.publish(
            payload.thread_id,
            {
                "type": "error",
                "message": str(e),
            },
        )
        await stream_manager.close(payload.thread_id)
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------
# FINAL POST
# -------------------------
@blog_router.post("/final_post")
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

    raise HTTPException(status_code=404, detail="Not found")


# -------------------------
# USER POSTS
# -------------------------
@blog_router.get("/user_posts/{user_id}")
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


# -------------------------
# STATUS
# -------------------------
@blog_router.get("/status/{thread_id}")
async def check_blog_status(thread_id: str, request: Request):
    """Return the current execution status for a blog workflow thread.

    Args:
        thread_id: Unique identifier for the workflow thread to inspect.
        request: FastAPI request used to access the database pool.

    Returns:
        dict: Current status, wait flag, and error message for the run.

    Raises:
        HTTPException: If the specified blog run does not exist.
    """
    pool = request.app.state.resources.pool

    run_data = await get_run(pool, thread_id)

    if not run_data:
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "status": run_data["status"],
        "is_waiting_for_you": run_data["status"] == "waiting_approval",
        "error": run_data["error_message"],
    }
