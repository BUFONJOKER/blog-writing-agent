from psycopg_pool import AsyncConnectionPool
from typing import Optional, Any, Dict, List
import json


async def save_output(
    pool: AsyncConnectionPool,
    thread_id: str,
    final_post_markdown: str,
    meta: Optional[Dict[str, Any]],
) -> None:
    """Creates or updates the final blog output."""
    query = """
    INSERT INTO public.blog_outputs (thread_id, final_post_markdown, meta)
    VALUES (%s, %s, %s::jsonb)
    ON CONFLICT (thread_id)
    DO UPDATE SET
        final_post_markdown = EXCLUDED.final_post_markdown,
        meta = EXCLUDED.meta;
    """
    meta_json = json.dumps(meta or {})

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (thread_id, final_post_markdown, meta_json))


async def get_output(
    pool: AsyncConnectionPool, thread_id: str
) -> Optional[Dict[str, Any]]:
    """Fetch a specific blog output by thread_id, including user_id."""

    # We JOIN with blog_runs to get the user_id associated with this thread
    query = """
    SELECT
        o.thread_id,
        r.user_id,
        o.final_post_markdown,
        o.meta,
        o.created_at
    FROM public.blog_outputs o
    JOIN public.blog_runs r ON o.thread_id = r.thread_id
    WHERE o.thread_id = %s
    LIMIT 1;
    """

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (thread_id,))
            row = await cur.fetchone()
            if row:
                keys = [
                    "thread_id",
                    "user_id",
                    "final_post_markdown",
                    "meta",
                    "created_at",
                ]
                return dict(zip(keys, row))
            return None


async def get_all_outputs_of_user(
    pool: AsyncConnectionPool, user_id: str
) -> List[Dict[str, Any]]:
    """Fetches all blog outputs belonging to a specific user_id."""

    # JOIN is required here because blog_outputs doesn't have user_id directly
    query = """
            SELECT
        o.thread_id,
        r.user_id,
        o.final_post_markdown,
        o.meta,
        o.created_at
        FROM public.blog_outputs o
        JOIN public.blog_runs r ON o.thread_id = r.thread_id
        WHERE r.user_id = %s
        ORDER BY o.created_at DESC;
    """

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (user_id,))
            rows = await cur.fetchall()
            keys = ["thread_id", "user_id", "final_post_markdown", "meta", "created_at"]
            return [dict(zip(keys, row)) for row in rows]
