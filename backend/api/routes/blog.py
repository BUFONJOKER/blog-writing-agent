from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from agent.main import agent, finalize_workflow
import asyncio
import uuid
from db.crud.blog_runs import create_blog_run, update_run_status, utc_now
from langgraph.types import Command
from db.crud.blog_outputs import get_output, get_all_outputs_of_user

blog_router = APIRouter(prefix="/blog", tags=["Blog Generation"])

class BlogRequest(BaseModel):
    user_id: str = Field(..., example="user123")
    prompt: str = Field(..., example="Write a blog about the benefits of AI for small businesses.")

@blog_router.post("/generate")
async def generate_blog(payload: BlogRequest, request: Request):

    thread_id = str(uuid.uuid4())

    # Access the shared resources from the app state
    resources = request.app.state.resources

    asyncio.create_task(
        agent(
            workflow=resources.workflow,
            pool=resources.pool,
            user_id=payload.user_id,
            thread_id=thread_id,
            prompt=payload.prompt
        )
    )

    return {
        "user_id": payload.user_id,
        "thread_id": thread_id,
        "status": "processing"
    }

class ReviewRequest(BaseModel):
    thread_id: str = Field(..., example="thread123")
    approved: bool = Field(..., example=True)

@blog_router.post("/review")
async def review_blog(payload: ReviewRequest, request: Request):
    '''This endpoint will be called by the frontend when the user approves or rejects at human review step. It will update the workflow state accordingly to either continue the workflow or stop it based on user feedback.'''

    resources = request.app.state.resources

    # Here you would implement the logic to update the workflow state based on the review feedback.

    config = {
        "configurable": {"thread_id": payload.thread_id}
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
        await finalize_workflow(resources.workflow, config, resources.pool, payload.thread_id)

        return {"thread_id": payload.thread_id, "approved": payload.approved, "status": "completed",'message': "Workflow completed successfully."}

    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while processing the review.", details=str(e))

class FinalPostRequest(BaseModel):
    user_id: str = Field(..., example="user123")
    thread_id: str = Field(..., example="thread123")

@blog_router.get("/final_post")
async def get_final_post(payload: FinalPostRequest, request: Request):
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
        raise HTTPException(status_code=404, detail="Final post not found for the given thread_id and user_id.")