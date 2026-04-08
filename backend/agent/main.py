import asyncio
import sys
import io
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg_pool import AsyncConnectionPool
from agent.workflow import build_workflow
from agent.config import DB_URL

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

async def main():
    async with AsyncConnectionPool(
        conninfo=DB_URL,
        max_size=20,
        min_size=1,
        kwargs={"autocommit": True},
    ) as pool:

        checkpointer = AsyncPostgresSaver(pool)
        # run the setup to create necessary tables if they don't exist. Safe to run multiple times.
        # await checkpointer.setup()

        app = await build_workflow(checkpointer)

        config = {
            "configurable": {"thread_id": "40_final_blog_test_with_images"},
            "run_name": "blog_writing_agent_run_46",
        }

        initial_input = {
            "prompt": "Local LLMs for Privacy: Create a guide for non-technical small business owners on why they should run Ollama locally instead of using cloud APIs. Focus on data sovereignty and cost-benefit analysis."
        }

        try:
            async for event in app.astream(initial_input, config, stream_mode="values"):
                print(f"Node completed: {list(event.keys())}")
        except Exception as e:
            print(f"An error occurred during graph execution: {e}")

if __name__ == "__main__":
    asyncio.run(main())