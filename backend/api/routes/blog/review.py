from fastapi import APIRouter, Request, HTTPException
import asyncio
from langgraph.types import Command
from backend.db.crud.blog_runs import update_run_status, get_run
from api.schema.blog_states import ReviewRequest, FinalPostRequest
from agent.main import finalize_workflow

router = APIRouter()

# -------------------------
# REVIEW
# -------------------------
@router.post("/review")
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
