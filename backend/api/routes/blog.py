from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from agent.main import agent, finalize_workflow
import asyncio
import uuid
from db.crud.blog_runs import create_blog_run, update_run_status, utc_now, get_run
from langgraph.types import Command
from db.crud.blog_outputs import get_output, get_all_outputs_of_user

blog_router = APIRouter(prefix="/blog", tags=["Blog Generation"])


class BlogRequest(BaseModel):
    """Payload for starting a new blog generation workflow.

    Args:
        user_id: Unique identifier for the user requesting blog generation.
        prompt: Natural language topic/instruction used to generate the blog.

    Returns:
        BlogRequest: A validated request model instance.
    """

    user_id: str = Field(..., example="user123")
    prompt: str = Field(
        ..., example="Write a blog about the benefits of AI for small businesses."
    )


@blog_router.post("/generate")
async def generate_blog(payload: BlogRequest, request: Request):
    """Start blog generation in the background and return a tracking thread id.

    Args:
        payload: Request body containing the user id and prompt.
        request: FastAPI request object used to access shared app resources.

    Returns:
        dict: Processing metadata containing user id, thread id, and status.

    Raises:
        HTTPException: If initialization fails before the background task starts.
    """

    try:
        thread_id = str(uuid.uuid4())

        # Access the shared resources from the app state
        resources = request.app.state.resources

        run_name = (
            f"Blog Run - {payload.prompt[:30]}..."  # Truncate prompt for run name
        )

        resources.run_name = run_name  # Store run name in resources for later use

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
            "status": "processing",
        }
    except Exception as e:
        # This catches errors that happen BEFORE the background task starts
        # e.g. Database connection issues or resource unavailability
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize blog generation: {str(e)}"
        )


class ReviewRequest(BaseModel):
    """Payload for approving or rejecting a workflow at human-review step.

    Args:
        thread_id: Workflow thread identifier to resume.
        approved: Review decision. `True` continues workflow, `False` rejects.

    Returns:
        ReviewRequest: A validated request model instance.
    """

    thread_id: str = Field(..., example="thread123")
    approved: bool = Field(..., example=True)


@blog_router.post("/review")
async def review_blog(payload: ReviewRequest, request: Request):
    """Process human review input and resume workflow execution.

    Args:
        payload: Review decision payload containing thread id and approval flag.
        request: FastAPI request object used to access shared app resources.

    Returns:
        dict: Confirmation message indicating review has been accepted.

    Raises:
        HTTPException: If workflow resumption or processing fails.
    """

    resources = request.app.state.resources

    # Here you would implement the logic to update the workflow state based on the review feedback.

    config = {
        "configurable": {"thread_id": payload.thread_id},
        "run_name": resources.run_name,  # Use the run name stored in resources
    }

    # update the db to show we are running
    await update_run_status(
        pool=resources.pool,
        thread_id=payload.thread_id,
        status="running",
    )

    # resume the workflow execution based on user feedback

    try:
        async for event in resources.workflow.astream(
            Command(resume=payload.approved), config, stream_mode="values"
        ):
            pass

        # finalize the workflow and save output to database after workflow completion
        asyncio.create_task(
            finalize_workflow(
                resources.workflow, config, resources.pool, payload.thread_id
            )
        )

        return {"message": "Review received. Workflow will be updated accordingly."}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while processing the review.",
            details=str(e),
        )


class FinalPostRequest(BaseModel):
    """Payload for retrieving the final blog post for a specific workflow run.

    Args:
        user_id: User identifier used for ownership verification.
        thread_id: Workflow thread identifier for the generated blog run.

    Returns:
        FinalPostRequest: A validated request model instance.
    """

    user_id: str = Field(..., example="user123")
    thread_id: str = Field(..., example="thread123")


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
