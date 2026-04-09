import asyncio
import sys
import io
import uuid
# from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command
from psycopg_pool import AsyncConnectionPool
# from agent.workflow import build_workflow
# from agent.config import DB_URL
from db.crud.blog_runs import create_blog_run, update_run_status, utc_now
from db.crud.blog_outputs import save_output, get_output, get_all_outputs_of_user

# if sys.platform == "win32":
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
#     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


async def agent(workflow, pool:AsyncConnectionPool, user_id:str, prompt:str):
    # async with AsyncConnectionPool(
    #     conninfo=DB_URL,
    #     max_size=20,
    #     min_size=1,
    #     kwargs={"autocommit": True},
    # ) as pool:

        # checkpointer = AsyncPostgresSaver(pool)
        # Ensure tables exist
        # await checkpointer.setup()

        # app = await build_workflow(checkpointer)

        app = workflow

        thread_id = str(uuid.uuid4())
        # user_id = input("Enter your user ID: ")
        # prompt = input("Enter your blog post prompt: ")
        run_name = f"blog_writing_agent_run_{thread_id[:8]}"

        await create_blog_run(
            pool=pool,
            thread_id=thread_id,
            user_id=user_id,
            prompt=prompt,
            status="running",
            interrupt_type=None,
        )

        config = {
            "configurable": {"thread_id": thread_id},
            "run_name": run_name,
        }

        initial_input = {"prompt": prompt}

        # --- INITIAL EXECUTION ---
        try:
            async for event in app.astream(initial_input, config, stream_mode="values"):
                # Clean printing of current node
                if "_debug" in event:
                    print(
                        f"Node completed: {event.get('metadata', {}).get('langgraph_node')}"
                    )
        except Exception as e:
            print(f"An error occurred: {e}")
            await update_run_status(
                pool=pool,
                thread_id=thread_id,
                status="interrupted",
                interrupt_type="error",
                error_message=str(e),
            )
            return

        # --- HUMAN-IN-THE-LOOP / RESUME LOOP ---
        while True:
            state = await app.aget_state(config)

            # Check if the graph is paused at human_review (waiting for human decision)
            if state.next and "human_review" in state.next:
                print("\n=== AGENT WAITING FOR HUMAN REVIEW ===")
                # Display critic feedback from the interrupt
                feedback = state.values.get("critic_feedback", {})
                quality_score = state.values.get("quality_score", "N/A")
                issues = (
                    feedback.get("issues", []) if isinstance(feedback, dict) else []
                )
                suggestions = (
                    feedback.get("suggestions", [])
                    if isinstance(feedback, dict)
                    else []
                )

                print(f"\nQuality Score: {quality_score}/10")
                if issues:
                    print(f"\nIdentified Issues:")
                    for issue in issues:
                        print(f"  - {issue}")
                if suggestions:
                    print(f"\nSuggested Improvements:")
                    for suggestion in suggestions:
                        print(f"  - {suggestion}")

                approval = (
                    input("\n✓ Approve revisions and continue? (y/n): ")
                    .lower()
                    .startswith("y")
                )

                # Update database status
                await update_run_status(
                    pool=pool,
                    thread_id=thread_id,
                    status="waiting_approval",
                    interrupt_type="human_review",
                )

                # Update database to running
                await update_run_status(
                    pool=pool,
                    thread_id=thread_id,
                    status="running",
                    interrupt_type=None,
                )

                print("Resuming workflow...")
                # Stream the remaining execution after resuming
                try:
                    async for event in app.astream(
                        Command(resume=approval), config, stream_mode="values"
                    ):
                        pass
                except Exception as e:
                    print(f"Error during workflow resumption: {e}")
                    await update_run_status(
                        pool=pool,
                        thread_id=thread_id,
                        status="interrupted",
                        interrupt_type="error",
                        error_message=str(e),
                    )
                    return
            else:
                # No more steps or not at human_review (graph finished)
                break

        # --- FINALIZATION ---
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
        print("\nWorkflow complete. Output saved to database.")

        print()

        print("\n--- RETRIEVAL SECTION ---")
        print(
            "If you want to see the blog of any user with thread_id then enter user_id and thread_id\n"
        )
        search_user_id = input("Enter user ID to retrieve blog output: ").strip()
        search_thread_id = input(
            "Enter thread ID (or leave blank to see all blogs for this user): "
        ).strip()

        if search_thread_id and search_user_id:
            # Note: get_output only needs pool and thread_id based on our CRUD update
            output = await get_output(pool, search_thread_id)

            # Check if output exists AND belongs to the user entered
            if output and output["user_id"] == search_user_id:
                print(f"\nRetrieved Blog Post (Thread: {search_thread_id}):\n")
                print("-" * 30)
                print(output["final_post_markdown"])
                print("-" * 30)
            else:
                print(
                    f"No output found for thread_id={search_thread_id} belonging to user_id={search_user_id}."
                )

        elif search_user_id:
            outputs = await get_all_outputs_of_user(pool, search_user_id)
            if outputs:
                print(
                    f"\nRetrieved {len(outputs)} Blog Post(s) for user_id={search_user_id}:\n"
                )
                for i, post in enumerate(outputs, 1):
                    print(f"--- Post {i} (Thread: {post['thread_id']}) ---")
                    # Displaying title from meta if it exists
                    title = post.get("meta", {}).get("title", "Untitled")
                    print(f"Title: {title}")
                    print(f"Content Preview: {post['final_post_markdown'][:200]}...")
                    print("-" * 30)
            else:
                print(f"No outputs found for user_id={search_user_id}.")


if __name__ == "__main__":
    try:
        asyncio.run(agent())
    except KeyboardInterrupt:
        print("\nScript stopped by user.")
