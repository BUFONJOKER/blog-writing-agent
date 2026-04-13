from psycopg_pool import AsyncConnectionPool
from typing import Optional, Any, Dict
from datetime import datetime, timezone

async def create_user(
    pool: AsyncConnectionPool,
    user_id: str,
    email: str,
    hashed_password: str,
) -> None:
    query = """
    insert into public.user_data (user_id, email, hashed_password)
    values (%s, %s, %s)
    on conflict (user_id) do nothing;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (user_id, email, hashed_password))


async def update_password(
    pool: AsyncConnectionPool,
    user_id: str,
    hashed_password: str,
) -> None:

    user = await get_user(pool, user_id)
    if not user:
        raise ValueError("User not found")

    query = """
    update public.user_data
    set hashed_password = %s
    where user_id = %s;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (hashed_password, user_id))


async def get_user(
    pool: AsyncConnectionPool,
    user_id: str,
) -> Optional[Dict[str, Any]]:
    # Added "id" to the start of the SELECT to match your dictionary mapping
    query = """
    select id, email, hashed_password
    from public.user_data
    where thread_id = %s
    limit 1;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (user_id,))
            row = await cur.fetchone()
            if row:
                return {
                    "id": row[0],
                    "email": row[1],
                    "hashed_password": row[2]
                }
            return "User not found"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)