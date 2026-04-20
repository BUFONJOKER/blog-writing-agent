from fastapi import APIRouter, Request, HTTPException
import asyncio
import logging
from langgraph.types import Command
from db.crud.blog_runs import update_run_status, get_run
from api.schema.blog_states import ReviewRequest, FinalPostRequest
from agent.main import finalize_workflow

router = APIRouter()
logger = logging.getLogger(__name__)


# -------------------------
# REVIEW
# -------------------------
@router.post("/review")
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
            detail="Run is not awaiting review.",
        )

    graph_state = await resources.workflow.aget_state(config)
    if not graph_state.next or "human_review" not in graph_state.next:
        raise HTTPException(
            status_code=409,
            detail="No resumable human review checkpoint found for this thread.",
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
            except Exception as exc:
                logger.exception("Finalization failed after review", exc_info=exc)
                await update_run_status(
                    pool=resources.pool,
                    thread_id=payload.thread_id,
                    status="failed",
                    error_message="The workflow failed while finalizing the reviewed draft.",
                    interrupt_type="error",
                )
                await stream_manager.publish(
                    payload.thread_id,
                    {
                        "type": "error",
                        "message": "The workflow failed while finalizing the reviewed draft.",
                    },
                )
                await stream_manager.close(payload.thread_id)

        asyncio.create_task(_finalize_with_guard())

        return {"message": "Review processed"}

    except Exception as exc:
        logger.exception("Failed to resume workflow review", exc_info=exc)
        await update_run_status(
            pool=resources.pool,
            thread_id=payload.thread_id,
            status="failed",
            error_message="The workflow failed while processing review.",
            interrupt_type="error",
        )
        await stream_manager.publish(
            payload.thread_id,
            {
                "type": "error",
                "message": "The workflow failed while processing review.",
            },
        )
        await stream_manager.close(payload.thread_id)
        raise HTTPException(
            status_code=500, detail="Unable to process the review right now."
        )
