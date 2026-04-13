from psycopg_pool import AsyncConnectionPool
from db.crud.blog_runs import create_blog_run, update_run_status, utc_now
from db.crud.blog_outputs import save_output, get_output, get_all_outputs_of_user


async def agent(
    workflow,
    pool,
    user_id: str,
    thread_id: str,
    prompt: str,
    run_name: str,
):
    """Background agent execution - moved here from generate."""
    app = workflow
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
        async for event in app.astream(initial_input, config, stream_mode="updates"):
            pass  # Discard for background - SSE handles live updates

        state = await app.aget_state(config)
        if state.next and "human_review" in state.next:
            await update_run_status(
                pool=pool,
                thread_id=thread_id,
                status="waiting_approval",
                interrupt_type="human_review",
            )
        else:
            await finalize_workflow(app, config, pool, thread_id)

    except Exception as e:
        await update_run_status(
            pool=pool,
            thread_id=thread_id,
            status="failed",
            interrupt_type="error",
            error_message=str(e),
        )
        raise e



async def finalize_workflow(app, config, pool, thread_id):
    """Finalize workflow and save output."""
    state = await app.aget_state(config)
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
    await update_run_status(pool=pool, thread_id=thread_id, status="completed", completed_at=utc_now())