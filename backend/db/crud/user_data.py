from psycopg_pool import AsyncConnectionPool
from typing import Optional, Any, Dict
from datetime import datetime, timezone


async def create_user(
    pool: AsyncConnectionPool,
    user_id: str,
    email: str,
    hashed_password: str,
) -> None:
    """Create a new user record with a stored password hash.

    Args:
        pool: Shared PostgreSQL connection pool.
        user_id: Unique identifier for the user record.
        email: User email address used for login.
        hashed_password: Secure password hash to persist in the database.

    Returns:
        None: The user record is inserted into the database.
    """
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
    """Update a user's stored password hash.

    Args:
        pool: Shared PostgreSQL connection pool.
        user_id: Unique identifier for the user record.
        hashed_password: New secure password hash to store.

    Returns:
        None: The password hash is updated in the database.

    Raises:
        ValueError: If the user record does not exist.
    """

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
    """Fetch a user record by user identifier.

    Args:
        pool: Shared PostgreSQL connection pool.
        user_id: Unique identifier for the user record.

    Returns:
        Optional[Dict[str, Any]]: The user row when found, otherwise a
        sentinel value indicating the user was not found.
    """
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
                return {"id": row[0], "email": row[1], "hashed_password": row[2]}
            return "User not found"


def utc_now() -> datetime:
    """Return the current UTC timestamp for user-data operations.

    Args:
        None: This helper only reads the current system time.

    Returns:
        datetime: Timezone-aware UTC datetime value.
    """
    return datetime.now(timezone.utc)
