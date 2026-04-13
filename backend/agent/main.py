from typing import Any
from psycopg_pool import AsyncConnectionPool

from db.crud.blog_runs import create_blog_run, update_run_status, utc_now
from db.crud.blog_outputs import save_output


# -------------------------
# JSON SERIALIZER
# -------------------------
def to_json_serializable(obj: Any) -> Any:
    """Convert nested objects into JSON-serializable data.

    Args:
        obj: Arbitrary object, mapping, sequence, or scalar to normalize.

    Returns:
        Any: A JSON-safe structure or string representation of the input.
    """
    from pydantic import BaseModel

    if isinstance(obj, BaseModel):
        return obj.model_dump()
    elif isinstance(obj, dict):
        return {k: to_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_json_serializable(v) for v in obj]
    elif hasattr(obj, "__dict__"):
        return to_json_serializable(obj.__dict__)
    elif obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    else:
        return str(obj)


# -------------------------
# AGENT EXECUTION
# -------------------------
async def agent(
    workflow,
    pool: AsyncConnectionPool,
    stream_manager,
    user_id: str,
    thread_id: str,
    prompt: str,
    run_name: str,
):
    """Execute the blog-generation workflow and publish SSE events.

    Args:
        workflow: Compiled LangGraph workflow used to run the blog pipeline.
        pool: Shared PostgreSQL connection pool.
        stream_manager: Queue-backed stream publisher for SSE consumers.
        user_id: Identifier for the user who started the request.
        thread_id: Unique identifier for the workflow run.
        prompt: Original blog request prompt.
        run_name: Human-readable name for tracing and debugging.

    Returns:
        None: The workflow runs asynchronously and reports progress via SSE.
    """

    await create_blog_run(
        pool=pool,
        thread_id=thread_id,
        user_id=user_id,
        prompt=prompt,
        status="running",
        interrupt_type=None,
    )

    config = {"configurable": {"thread_id": thread_id}, "run_name": run_name}
    initial_input = {"prompt": prompt}

    try:
        # 🔥 STREAM EVENTS FROM WORKFLOW → PUSH TO QUEUE
        async for event in workflow.astream(
            initial_input, config, stream_mode="updates"
        ):
            await stream_manager.publish(
                thread_id,
                {
                    "type": "update",
                    "data": to_json_serializable(event),
                },
            )

        # -------------------------
        # CHECK STATE AFTER RUN
        # -------------------------
        state = await workflow.aget_state(config)

        if state.next and "human_review" in state.next:
            await update_run_status(
                pool=pool,
                thread_id=thread_id,
                status="waiting_approval",
                interrupt_type="human_review",
            )

            await stream_manager.publish(thread_id, {"type": "waiting_approval"})

        else:
            await finalize_workflow(workflow, config, pool, thread_id, stream_manager)

    except Exception as e:
        await update_run_status(
            pool=pool,
            thread_id=thread_id,
            status="failed",
            interrupt_type="error",
            error_message=str(e),
        )

        await stream_manager.publish(
            thread_id,
            {
                "type": "error",
                "message": str(e),
            },
        )

        await stream_manager.close(thread_id)

        raise e


# -------------------------
# FINALIZE
# -------------------------
async def finalize_workflow(workflow, config, pool, thread_id, stream_manager):
    """Persist the final blog output, update status, and end the stream.

    Args:
        workflow: Compiled LangGraph workflow used to inspect final state.
        config: LangGraph configuration containing the workflow thread id.
        pool: Shared PostgreSQL connection pool.
        thread_id: Unique identifier for the workflow run.
        stream_manager: Queue-backed stream publisher for SSE consumers.

    Returns:
        None: The final output is stored and the stream is closed.
    """
    state = await workflow.aget_state(config)

    final_md = state.values.get("final_post") or "No final post markdown found."

    await save_output(
        pool=pool,
        thread_id=thread_id,
        final_post_markdown=final_md,
        meta={
            "title": state.values.get("title"),
            "slug": state.values.get("slug"),
            "keywords_used": state.values.get("keywords_used"),
            "meta_description": state.values.get("meta_description"),
        },
    )

    await update_run_status(
        pool=pool,
        thread_id=thread_id,
        status="completed",
        completed_at=utc_now(),
    )

    await stream_manager.publish(thread_id, {"type": "completed"})

    await stream_manager.close(thread_id)
