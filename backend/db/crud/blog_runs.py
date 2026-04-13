from psycopg_pool import AsyncConnectionPool
from typing import Optional, Any, Dict, List
from datetime import datetime, timezone


async def create_blog_run(
    pool: AsyncConnectionPool,
    thread_id: str,
    user_id: str,
    prompt: str,
    status: str = "running",
    interrupt_type: Optional[str] = None,
) -> None:
    """Create a new blog run record for a workflow execution.

    Args:
        pool: Shared PostgreSQL connection pool.
        thread_id: Unique identifier for the workflow thread.
        user_id: Identifier for the user who started the run.
        prompt: Original blog request prompt.
        status: Initial run status to persist.
        interrupt_type: Optional interrupt classification for paused runs.

    Returns:
        None: The run record is inserted into the database.
    """
    query = """
    insert into public.blog_runs (thread_id, user_id, prompt, status, interrupt_type)
    values (%s, %s, %s, %s, %s)
    on conflict (thread_id) do nothing;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                query, (thread_id, user_id, prompt, status, interrupt_type)
            )


async def update_run_status(
    pool: AsyncConnectionPool,
    thread_id: str,
    status: str,
    interrupt_type: Optional[str] = None,
    error_message: Optional[str] = None,
    completed_at: Optional[datetime] = None,  # Changed to datetime for consistency
) -> None:
    """Update the persisted status and metadata for a blog run.

    Args:
        pool: Shared PostgreSQL connection pool.
        thread_id: Unique identifier for the workflow thread.
        status: New lifecycle status to store.
        interrupt_type: Optional interrupt label when the run is paused.
        error_message: Optional error text to persist for failed runs.
        completed_at: Optional completion timestamp for finished runs.

    Returns:
        None: The status row is updated in place.
    """
    query = """
    update public.blog_runs
    set status = %s,
        interrupt_type = %s,
        error_message = %s,
        completed_at = coalesce(%s, completed_at),
        updated_at = now()
    where thread_id = %s;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                query, (status, interrupt_type, error_message, completed_at, thread_id)
            )


async def get_run(
    pool: AsyncConnectionPool,
    thread_id: str,
) -> Optional[Dict[str, Any]]:
    """Fetch a single blog run record by thread identifier.

    Args:
        pool: Shared PostgreSQL connection pool.
        thread_id: Unique identifier for the workflow thread.

    Returns:
        Optional[Dict[str, Any]]: The matching run record, or None if absent.
    """
    # Added "id" to the start of the SELECT to match your dictionary mapping
    query = """
    select id, thread_id, user_id, prompt, status, interrupt_type, error_message, created_at, updated_at, completed_at
    from public.blog_runs
    where thread_id = %s
    limit 1;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (thread_id,))
            row = await cur.fetchone()
            if row:
                return {
                    "id": row[0],
                    "thread_id": row[1],
                    "user_id": row[2],
                    "prompt": row[3],
                    "status": row[4],
                    "interrupt_type": row[5],
                    "error_message": row[6],
                    "created_at": row[7],
                    "updated_at": row[8],
                    "completed_at": row[9],
                }
            return None


async def list_runs_for_user(
    pool: AsyncConnectionPool, user_id: str, limit: int = 50, offset: int = 0
) -> List[Dict[str, Any]]:
    """List recent blog runs for a specific user.

    Args:
        pool: Shared PostgreSQL connection pool.
        user_id: User identifier whose runs should be returned.
        limit: Maximum number of rows to return.
        offset: Row offset for pagination.

    Returns:
        List[Dict[str, Any]]: Blog run rows ordered from newest to oldest.
    """
    query = """
    select thread_id, prompt, status, interrupt_type, error_message, created_at, updated_at, completed_at
    from public.blog_runs
    where user_id = %s
    order by created_at desc
    limit %s offset %s;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (user_id, limit, offset))
            rows = await cur.fetchall()
            # Fixed mapping to match the 8 columns selected above
            return [
                {
                    "thread_id": row[0],
                    "prompt": row[1],
                    "status": row[2],
                    "interrupt_type": row[3],
                    "error_message": row[4],
                    "created_at": row[5],
                    "updated_at": row[6],
                    "completed_at": row[7],
                }
                for row in rows
            ]


def utc_now() -> datetime:
    """Return the current UTC timestamp.

    Args:
        None: This helper reads the current system time only.

    Returns:
        datetime: Timezone-aware UTC datetime for persistence.
    """
    return datetime.now(timezone.utc)
