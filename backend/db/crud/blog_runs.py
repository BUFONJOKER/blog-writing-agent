import uuid
from psycopg_pool import AsyncConnectionPool
from typing import Optional, Any


async def create_blog_run(
    pool: AsyncConnectionPool,
    thread_id: str,
    user_id: str,
    prompt: str,
    status: str = "running",
    interrupt_type: Optional[str] = None,
) -> None:

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