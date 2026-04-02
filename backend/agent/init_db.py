import asyncio
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agent.config import Config
import sys


# --- FIX FOR WINDOWS ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# -----------------------



async def setup_db():
    # CRITICAL: Add kwargs={"autocommit": True} here
    async with AsyncConnectionPool(
        conninfo=Config.DB_URL,
        max_size=20,
        kwargs={"autocommit": True}
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)

        print("Connecting to Supabase and setting up tables...")
        await checkpointer.setup()
        print("Tables created successfully!")

if __name__ == "__main__":
    asyncio.run(setup_db())