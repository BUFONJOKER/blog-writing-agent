import asyncio
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agent.workflow import build_workflow
from agent.config import DB_URL
import sys
import io

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # Force stdout to use utf-8 to prevent 'charmap' errors on Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import os

os.environ["PSYCOPG_IMPL"] = "python"

# Your existing imports continue below...
from psycopg_pool import AsyncConnectionPool


async def main():
    DB_URI = DB_URL

    async with AsyncConnectionPool(
        conninfo=DB_URI, max_size=20, kwargs={"autocommit": True}
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        # 1. Compile the graph with memory
        app = await build_workflow(checkpointer)

        # 2. Thread ID identifies this specific conversation
        config = {
            "configurable": {"thread_id": "28_final_blog_test_with_images"},
            "run_name": "blog_writing_agent_run_34",
        }  # You can generate a unique thread_id for each conversation or use a fixed one for testing

        # 3. Start the process and stream events until completion.
        initial_input = {
            "prompt": "Local LLMs for Privacy: Create a guide for non-technical small business owners on why they should run Ollama locally instead of using cloud APIs. Focus on data sovereignty and cost-benefit analysis."
        }
        async for event in app.astream(initial_input, config, stream_mode="values"):
            print(event)

        # 4. Print final state summary after workflow completion.
        state = await app.aget_state(config)
        print("\n--- FINAL STATE SUMMARY ---")
        print(f"status: {state.values.get('status')}")
        print(f"title: {state.values.get('blog_title')}")


if __name__ == "__main__":
    asyncio.run(main())
