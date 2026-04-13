from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
import asyncio
import uuid
import json

from langgraph.types import Command

from db.crud.blog_runs import update_run_status, get_run
from db.crud.blog_outputs import get_output, get_all_outputs_of_user

from api.schema.blog_states import BlogRequest, ReviewRequest, FinalPostRequest
from agent.main import agent, finalize_workflow

from api.routes.blog import blog_router


# -------------------------
# GENERATE BLOG
# -------------------------
@blog_router.post("/generate")
async def generate_blog(payload: BlogRequest, request: Request):
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


# -------------------------
# REVIEW
# -------------------------
@blog_router.post("/review")
async def review_blog(payload: ReviewRequest, request: Request):
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
    pool = request.app.state.resources.pool

    run_data = await get_run(pool, thread_id)

    if not run_data:
        raise HTTPException(status_code=404, detail="Not found")

    return {
        "status": run_data["status"],
        "is_waiting_for_you": run_data["status"] == "waiting_approval",
        "error": run_data["error_message"],
    }
