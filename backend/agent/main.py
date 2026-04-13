from psycopg_pool import AsyncConnectionPool
from db.crud.blog_runs import create_blog_run, update_run_status, utc_now
from db.crud.blog_outputs import save_output


async def agent(
    workflow,
    pool: AsyncConnectionPool,
    user_id: str,
    thread_id: str,
    prompt: str,
    run_name: str,
):
    """Start or resume the blog workflow and return an async event stream.

    Args:
        workflow: The LangGraph workflow instance to execute.
        pool: The database connection pool used for run tracking.
        user_id: The ID of the user initiating the blog generation.
        thread_id: The workflow thread ID used to resume state.
        prompt: The blog prompt provided by the user.
        run_name: The run name used for traceability.

    Returns:
        An async generator that streams workflow updates.
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

    # Resume from an existing thread state if present; otherwise start with the prompt.
    state = await workflow.aget_state(config)

    initial_input = {"prompt": prompt} if not state.values else None

    return workflow.astream(initial_input, config, stream_mode="updates")


async def finalize_workflow(workflow, config, pool, thread_id):
    """Persist the final post and mark the run as completed."""

    state = await workflow.aget_state(config)

    final_md = state.values.get("final_post", "No final post markdown found.")
    metadata = {
        "title": state.values.get("title", "Untitled"),
        "slug": state.values.get("slug", ""),
        "keywords_used": state.values.get("keywords_used", []),
        "meta_description": state.values.get("meta_description", ""),
    }

    await save_output(
        pool=pool,
        thread_id=thread_id,
        final_post_markdown=final_md,
        meta=metadata,
    )

    await update_run_status(
        pool=pool,
        thread_id=thread_id,
        status="completed",
        completed_at=utc_now(),
    )
