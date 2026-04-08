from psycopg_pool import AsyncConnectionPool
from typing import Optional, Any, Dict
import json


async def save_output(
    pool: AsyncConnectionPool,
    thread_id: str,
    final_post_markdown: str,
    meta: Optional[Dict[str, Any]],
) -> None:
    """Create or update the final blog output for a workflow thread.

    Stores the generated markdown and metadata in `public.blog_outputs`.
    If an entry for the same `thread_id` already exists, it is updated
    (upsert behavior) to keep only the latest output.

    Args:
        pool: Database connection pool used to execute the query.
        thread_id: Unique workflow thread identifier associated with the output.
        final_post_markdown: Final blog content in markdown format.
        meta: Optional metadata dictionary (for example, model info or run stats).

    Returns:
        None. Persists the output row in the database.
    """

    query = """
    insert into public.blog_outputs (thread_id, final_post_markdown, meta)
    values (%s, %s, %s::jsonb)
    on conflict (thread_id)
    do update set final_post_markdown = EXCLUDED.final_post_markdown, meta = EXCLUDED.meta;
    """

    meta_json = json.dumps(
        meta or {}
    )  # Convert meta dict to JSON string, handle None case

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                query,
                (
                    thread_id,
                    final_post_markdown,
                    meta_json,
                ),
            )


async def get_output(
    pool: AsyncConnectionPool, thread_id: str
) -> Optional[Dict[str, Any]]:
    """Fetch the saved blog output record for a specific workflow thread.

    Args:
        pool: Database connection pool used to execute the query.
        thread_id: Unique workflow thread identifier to look up.

    Returns:
        A dictionary containing `thread_id`, `final_post_markdown`, `meta`,
        and `created_at` when a record exists; otherwise None.
    """

    query = """
    select thread_id, final_post_markdown, meta, created_at
    from public.blog_outputs
    where thread_id = %s
    limit 1;
    """

    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (thread_id,))
            row = await cur.fetchone()
            if row:
                keys = ["thread_id", "final_post_markdown", "meta", "created_at"]
                return dict(zip(keys, row))
            else:
                return None
