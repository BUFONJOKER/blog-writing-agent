import asyncio
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agent.workflow import build_workflow
from agent.config import DB_URL, DB_POOLER_URL
import sys
import io
import socket
from urllib.parse import urlparse

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # Force stdout to use utf-8 to prevent 'charmap' errors on Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import os

os.environ["PSYCOPG_IMPL"] = "python"

# Your existing imports continue below...
from psycopg_pool import AsyncConnectionPool


def _host_has_ipv4(hostname: str) -> bool:
    """Return True if hostname resolves to at least one IPv4 address."""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        return False
    return any(info[0] == socket.AF_INET for info in infos)


def _ensure_sslmode(conninfo: str) -> str:
    """Supabase requires SSL; enforce it if missing."""
    if "sslmode=" in conninfo:
        return conninfo
    separator = "&" if "?" in conninfo else "?"
    return f"{conninfo}{separator}sslmode=require"


def resolve_conninfo() -> str:
    """Pick a reachable Postgres URL, preferring direct URL when IPv4 is available."""
    if not DB_URL:
        raise RuntimeError("DB_URL is not set. Please configure backend/.env")

    direct = _ensure_sslmode(DB_URL)
    hostname = urlparse(direct).hostname
    if hostname and _host_has_ipv4(hostname):
        return direct

    if DB_POOLER_URL:
        print(
            "Direct DB host appears IPv6-only from this environment. "
            "Falling back to DB_POOLER_URL."
        )
        return _ensure_sslmode(DB_POOLER_URL)

    raise RuntimeError(
        "Direct DB host resolves without IPv4 in this environment. "
        "Set DB_POOLER_URL (Supabase Session/Transaction Pooler URL) in backend/.env "
        "or use an IPv6-capable network."
    )


async def main():
    conninfo = resolve_conninfo()

    async with AsyncConnectionPool(
        conninfo=conninfo,
        max_size=10,
        min_size=1,
        kwargs={
            "autocommit": True,
            "connect_timeout": 10,
            "prepare_threshold": None,
        },
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)

        # Optional: Ensure tables exist (only needs to run once ever)
        # await checkpointer.setup()

        app = await build_workflow(checkpointer)

        config = {
            "configurable": {"thread_id": "34_final_blog_test_with_images"},
            "run_name": "blog_writing_agent_run_40",
        }

        initial_input = {
            "prompt": "Local LLMs for Privacy: Create a guide for non-technical small business owners on why they should run Ollama locally instead of using cloud APIs. Focus on data sovereignty and cost-benefit analysis."
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
