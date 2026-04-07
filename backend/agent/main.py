import asyncio
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agent.workflow import build_workflow
from agent.config import DB_URL
import sys
import io
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # Force stdout to use utf-8 to prevent 'charmap' errors on Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
import os
os.environ["PSYCOPG_IMPL"] = "python"

# Your existing imports continue below...
from psycopg_pool import AsyncConnectionPool

async def main():
    DB_URI = DB_URL

    async with AsyncConnectionPool(conninfo=DB_URI, max_size=20, kwargs={"autocommit": True}) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        # 1. Compile the graph with memory
        app = await build_workflow(checkpointer)

        # 2. Thread ID identifies this specific conversation
        config = {"configurable": {"thread_id": "14_final_blog_test_with_images"},'run_name': "blog_writing_agent_run_20"}

        # 3. Start the process
        initial_input = {"prompt": "Write a blog post about the benefits of using MCP servers for Minecraft."}
        async for event in app.astream(initial_input, config, stream_mode="values"):
            print(event)

        # --- THE GRAPH IS NOW INTERRUPTED AFTER IMAGE_GENERATION_NODE ---

        # 4. Fetch the state to show the human the plan
        state = await app.aget_state(config)
        print("\n--- PROPOSED PLAN ---")
        print(state.values.get("blog_plan"))

        # 5. Human Input
        feedback = input("\nType 'proceed' to start writing, or enter feedback to change the plan: ")

        if feedback.lower() != "proceed":
            # Update the state with feedback and go back to a previous node if necessary
            await app.aupdate_state(config, {"human_feedback": feedback}, as_node="image_planner_node")
            print("Feedback saved. You might want to re-run the image planner or resume.")

        # 6. Resume execution
        # Passing None tells LangGraph to look at the last checkpoint and continue
        async for event in app.astream(None, config, stream_mode="values"):
            # Replace your current print(event) with this:
            try:
                print(event)
            except UnicodeEncodeError:
                # Fallback: encode to ascii and ignore errors just for the console display
                print(str(event).encode('ascii', 'ignore').decode('ascii'))

if __name__ == "__main__":
    asyncio.run(main())