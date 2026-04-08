from psycopg_pool import AsyncConnectionPool
from typing import Optional, Any
from datetime import datetime, timezone


async def create_blog_run(
    pool: AsyncConnectionPool,
    thread_id: str,
    user_id: str,
    prompt: str,
    status: str = "running",
    interrupt_type: Optional[str] = None,
) -> None:
    """Create a new blog run entry (idempotent via upsert).

    If a run with the same thread_id already exists, skips creation instead of
    overwriting, ensuring safe re-entrancy and no accidental data loss.

    Args:
        pool: Database connection pool.
        thread_id: Unique identifier for the blog run (workflow thread).
        user_id: User ID associated with the blog run.
        prompt: The initial prompt/request for blog generation.
        status: Current run status (default: "running").
        interrupt_type: Optional interrupt reason (e.g., "user_cancelled", "error").

    Returns:
        None. Inserts or skips entry based on thread_id conflict.
    """

    query = """
    insert into public.blog_runs (id, thread_id, user_id, prompt, status, interrupt_type)
    values (%s, %s, %s, %s, %s, %s)
    on conflict (thread_id) do nothing;
    """

    async with pool.connection() as conn:

        async with conn.cursor() as cur:

            await cur.execute(
                query,
                (
                    thread_id,
                    user_id,
                    prompt,
                    status,
                    interrupt_type,
                ),
            )


async def update_run_status(
    pool: AsyncConnectionPool,
    thread_id: str,
    status: str,
    interrupt_type: Optional[str] = None,
    error_message: Optional[str] = None,
    completed_at: Optional[str] = None,
) -> None:
    """Update the status and metadata of an existing blog run.

    Updates the status, interrupt type, error message, and completion timestamp.
    Only updates fields that are explicitly provided; others remain unchanged.

    Args:
        pool: Database connection pool.
        thread_id: Unique identifier for the blog run to update.
        status: New status value (e.g., "running", "completed", "failed").
        interrupt_type: Optional interrupt reason if run was interrupted.
        error_message: Optional error details if run failed.
        completed_at: Optional completion timestamp; if None, preserved as-is.

    Returns:
        None. Updates the specified run in the database.
    """

    query = """
    update public.blog_runs
    set status = %s, interrupt_type = %s
    error_message = %s,
    completed_at = coalesce(%s, completed_at),
    updated_at = now()
    where thread_id = %s;
    """

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                query,
                (
                    status,
                    interrupt_type,
                    error_message,
                    completed_at,
                    thread_id,
                ),
            )


async def get_run(
    pool: AsyncConnectionPool,
    thread_id: str,
) -> Optional[dict[str, Any]]:
    """Retrieve a single blog run by its thread ID.

    Returns a dictionary with run details (thread_id, user_id, prompt, status, etc.)
    or None if no run is found.

    Args:
        pool: Database connection pool.
        thread_id: Unique identifier for the blog run to retrieve.

    Returns:
        Dictionary containing run details (thread_id, user_id, prompt, status, interrupt_type,
        error_message, created_at, updated_at), or None if no matching run exists.
    """

    query = """
    select thread_id, user_id, prompt, status, interrupt_type, error_message, created_at, updated_at, completed_at
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
                }
            return None


async def list_runs_for_user(
    pool: AsyncConnectionPool, user_id: str, limit: int = 50, offset: int = 0
) -> list[dict[str, Any]]:
    """Fetch all blog runs for a user, paginated and ordered by creation date (newest first).

    Args:
        pool: Database connection pool.
        user_id: User identifier to filter runs.
        limit: Maximum number of runs to return (default: 50).
        offset: Number of runs to skip for pagination (default: 0).

    Returns:
        List of dictionaries containing run details (thread_id, prompt, status, etc.).
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
            return [
                {
                    "thread_id": row[0],
                    "prompt": row[1],
                    "status": row[2],
                    "interrupt_type": row[3],
                    "error_message": row[4],
                    "created_at": row[5],
                    "updated_at": row[6],
                }
                for row in rows
            ]


def utc_now() -> datetime:
    """Return the current UTC datetime.

    Useful for timestamping database operations and ensuring consistent timezone handling.

    Args:
        None.

    Returns:
        Current date and time in UTC timezone.
    """
    return datetime.now(timezone.utc)
