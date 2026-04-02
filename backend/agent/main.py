import asyncio
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agent.workflow import build_workflow
from agent.config import Config
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    DB_URI = Config.DB_URL

    async with AsyncConnectionPool(conninfo=DB_URI, max_size=20, kwargs={"autocommit": True}) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        # 1. Compile the graph with memory
        app = await build_workflow(checkpointer)

        # 2. Thread ID identifies this specific conversation
        config = {"configurable": {"thread_id": "blog_123"}}

        # 3. Start the process
        initial_input = {"prompt": "Write a blog post about 2026 MLOps"}
        async for event in app.astream(initial_input, config, stream_mode="values"):
            print(event)

        # --- THE GRAPH IS NOW INTERRUPTED AFTER PLANNER_NODE ---

        # 4. Fetch the state to show the human the plan
        state = await app.aget_state(config)
        print("\n--- PROPOSED PLAN ---")
        print(state.values.get("blog_plan"))

        # 5. Human Input
        feedback = input("\nType 'proceed' to start writing, or enter feedback to change the plan: ")

        if feedback.lower() != "proceed":
            # Update the state with feedback and go back to a previous node if necessary
            await app.aupdate_state(config, {"human_feedback": feedback}, as_node="planner_node")
            print("Feedback saved. You might want to re-run the planner or resume.")

        # 6. Resume execution
        # Passing None tells LangGraph to look at the last checkpoint and continue
        async for event in app.astream(None, config, stream_mode="values"):
            print(event)

if __name__ == "__main__":
    asyncio.run(main())