from psycopg_pool import AsyncConnectionPool
from db.crud.blog_runs import create_blog_run, update_run_status, utc_now
from db.crud.blog_outputs import save_output, get_output, get_all_outputs_of_user


async def agent(
    workflow,
    pool: AsyncConnectionPool,
    user_id: str,
    thread_id: str,
    prompt: str,
    run_name: str,
):
    """Main function to run the agent workflow for blog generation.

    Args:
        workflow: The LangGraph workflow instance to execute.
        pool: An instance of AsyncConnectionPool for database interactions.
        user_id: The ID of the user initiating the blog generation.
        prompt: The blog post prompt provided by the user.

    This function executes the workflow, handles human-in-the-loop interactions, and manages database updates for the blog generation process.
    """

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

    # --- INITIAL EXECUTION ---
    try:
        # Stream the execution of the workflow with the initial prompt
        # and it will stop at human_review node and wait for human feedback and approval to continue
        async for event in app.astream(initial_input, config, stream_mode="values"):
            pass

        state = await app.aget_state(config)

        if state.next and "human_review" in state.next:
            # the workflow is paused at human_review node, waiting for human feedback and approval to continue
            await update_run_status(
                pool=pool,
                thread_id=thread_id,
                status="waiting_approval",
                interrupt_type="human_review",
            )

        else:
            # workflow finished without hitting human_review node, finalize the workflow and save output to database
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
        # Update database status to failed if any error occurs during execution

    return {"thread_id": thread_id}


async def finalize_workflow(app, config, pool, thread_id):
    """Function to finalize the workflow after completion and save the output to the database."""

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

    await update_run_status(
        pool=pool, thread_id=thread_id, status="completed", completed_at=utc_now()
    )

