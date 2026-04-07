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
    # 1. Ensure you use the DIRECT connection string (Port 5432)
    # instead of the Transaction Pooler (Port 6543).
    DB_URI = DB_URL

    async with AsyncConnectionPool(
        conninfo=DB_URI,
        max_size=20,
        # Adding keepalives and disabling prepared statements for Supabase stability
        kwargs={
            "autocommit": True,
            "prepare_threshold": None,  # Crucial for Supabase Pooler compatibility
            "keepalives": 1,           # Sends a "heartbeat" to prevent timeout
            "keepalives_idle": 30,     # If idle for 30s, send heartbeat
            "keepalives_interval": 10,
            "keepalives_count": 5
        }
    ) as pool:
        # Use the AsyncPostgresSaver with the pool
        # It's recommended to call .setup() once if tables aren't created yet
        checkpointer = AsyncPostgresSaver(pool)

        # Optional: Ensure tables exist (only needs to run once ever)
        # await checkpointer.setup()

        app = await build_workflow(checkpointer)

        config = {
            "configurable": {"thread_id": "30_final_blog_test_with_images"},
            "run_name": "blog_writing_agent_run_36",
        }

        initial_input = {
            "prompt": "Local LLMs for Privacy: Create a guide for non-technical small business owners..."
        }

        try:
            async for event in app.astream(initial_input, config, stream_mode="values"):
                # Printing 'event' can be very messy if it contains the whole state.
                # Just printing the keys or a status update is often cleaner.
                print(f"Node completed: {list(event.keys())}")

        except Exception as e:
            print(f"An error occurred during graph execution: {e}")


if __name__ == "__main__":
    asyncio.run(main())
