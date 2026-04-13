import asyncio
import uuid
import json
from urllib.parse import urlencode
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from agent.main import agent, finalize_workflow
from db.crud.blog_runs import update_run_status, utc_now, get_run
from langgraph.types import Command
from db.crud.blog_outputs import get_output, get_all_outputs_of_user
from api.schema.blog_request import BlogRequest
from api.schema.review_request import ReviewRequest
from api.schema.final_post_request import FinalPostRequest

blog_router = APIRouter(prefix="/blog", tags=["Blog Generation"])


# Create a new blog run ID and return the stream URL the client should open.
@blog_router.post("/generate")
async def generate_blog(payload: BlogRequest, request: Request):
    """Initialize a blog generation request.

    Args:
        payload: Blog generation request containing the user ID and prompt.
        request: FastAPI request object.

    Returns:
        dict: Initialization payload with the thread ID, status, and stream URL.
    """

    thread_id = str(uuid.uuid4())
    query_string = urlencode({"prompt": payload.prompt, "user_id": payload.user_id})

    return {
        "user_id": payload.user_id,
        "thread_id": thread_id,
        "status": "initialized",
        "stream_url": f"/blog/{thread_id}/stream?{query_string}",
    }


# Stream workflow events back to the client as Server-Sent Events.
@blog_router.get("/{thread_id}/stream")
async def stream_blog_output(
    thread_id: str, prompt: str, user_id: str, request: Request
):
    '''
    Stream blog generation updates for a given workflow thread.'''

    resources = request.app.state.resources
    run_name = f"blog_run_{thread_id}_{user_id}_{utc_now().isoformat()}"
    config = {"configurable": {"thread_id": thread_id}, "run_name": run_name}

    async def event_generator():
        try:
            stream = await agent(
                workflow=resources.workflow,
                pool=resources.pool,
                user_id=user_id,
                thread_id=thread_id,
                prompt=prompt,
                run_name=run_name,
            )

            while True:
                try:
                    event = await asyncio.wait_for(anext(stream), timeout=60.0)
                    yield f"data: {json.dumps({'type': 'node_update', 'data': event})}\n\n"

                except StopAsyncIteration:
                    state = await resources.workflow.aget_state(config)

                    if state.next and "human_review" in state.next:
                        # Mark the run as waiting for review before pausing the stream.
                        await update_run_status(
                            pool=resources.pool,
                            thread_id=thread_id,
                            status="waiting_approval",
                            interrupt_type="human_review",
                        )
                        yield f"data: {json.dumps({'type': 'waiting_for_review', 'message': 'Workflow is paused for human review'})}\n\n"
                    else:
                        await finalize_workflow(
                            resources.workflow, config, resources.pool, thread_id
                        )
                        yield f"data: {json.dumps({'type': 'workflow_complete', 'message': 'Workflow execution completed'})}\n\n"
                    break

        except Exception as e:
            await update_run_status(
                pool=resources.pool,
                thread_id=thread_id,
                status="failed",
                interrupt_type="error",
                error_message=str(e),
            )
            yield f"data: {json.dumps({'type': 'error', 'message': 'An error occurred during workflow execution', 'details': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# Resume a paused workflow after the user submits a review decision.
@blog_router.post("/review")
async def review_blog(payload: ReviewRequest, request: Request):
    """Resume a paused blog workflow using the review decision.

    Args:
        payload: Review decision payload containing the thread ID and approval flag.
        request: FastAPI request object used to access shared app resources.

    Returns:
        dict: Confirmation message that the review was processed.

    Raises:
        HTTPException: If workflow resumption fails.
    """

    resources = request.app.state.resources

    config = {
        "configurable": {"thread_id": payload.thread_id},
        "run_name": f"blog_run_{payload.thread_id}",
    }

    await update_run_status(
        pool=resources.pool,
        thread_id=payload.thread_id,
        status="running",
    )

    try:
        await resources.workflow.ainvoke(Command(resume=payload.approved), config)

        return {
            "status": "success",
            "message": "Review processed. Re-connect to the stream to see the remaining steps.",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# Return the persisted status for a blog run.
@blog_router.get("/status/{thread_id}")
async def check_blog_status(thread_id: str, request: Request):
    """Fetch the current execution status for a blog run.

    Args:
        thread_id: Workflow thread identifier to inspect.
        request: FastAPI request object used to access the database pool.

    Returns:
        dict: Status payload including the current state, wait flag, and error.

    Raises:
        HTTPException: If the blog run does not exist.
    """

    pool = request.app.state.resources.pool

    run_data = await get_run(pool, thread_id)

    if not run_data:
        raise HTTPException(status_code=404, detail="Blog run not found")

    return {
        "status": run_data["status"],
        "is_waiting_for_you": run_data["status"] == "waiting_approval",
        "error": run_data["error_message"],
    }


# Return the final stored post only when it belongs to the requesting user.
@blog_router.post("/final_post")
async def get_final_post(payload: FinalPostRequest, request: Request):
    """Return the final blog output for the authenticated user.

    Args:
        payload: Request body containing the user ID and workflow thread ID.
        request: FastAPI request object used to access the database pool.

    Returns:
        dict: Final blog markdown and metadata for the requested thread.

    Raises:
        HTTPException: If no matching output is found for the user and thread ID.
    """

    pool = request.app.state.resources.pool
    output = await get_output(pool, payload.thread_id)

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


# Return all stored blog posts for the given user.
@blog_router.get("/user_posts/{user_id}")
async def get_user_posts(user_id: str, request: Request):
    """Fetch all blog posts generated by a specific user.

    Args:
        user_id: Identifier for the user whose posts to retrieve.
        request: FastAPI request object used to access the database pool.

    Returns:
        list: A list of blog posts associated with the user.

    Raises:
        HTTPException: If no posts are found for the user.
    """

    pool = request.app.state.resources.pool

    posts = await get_all_outputs_of_user(pool, user_id)

    if not posts:
        raise HTTPException(
            status_code=404,
            detail="No blog posts found for the given user.",
        )

    return posts
