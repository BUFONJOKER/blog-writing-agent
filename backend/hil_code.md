No problem — start with **minimal DB code** (async, psycopg-pool), since you’re already using that for `AsyncPostgresSaver`. Below is a copy‑pasteable baseline you can drop into `backend/db/`, then wire into your existing `main.py`.

## 1) Create these folders/files

```
backend/db/
  __init__.py
  crud/
    __init__.py
    blog_runs.py
    blog_outputs.py
```

---

## 2) Create the CRUD code (async, Supabase Postgres)

### `backend/db/crud/blog_runs.py`

```python
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, List, Dict

from psycopg_pool import AsyncConnectionPool

async def create_blog_run(
    pool: AsyncConnectionPool,
    thread_id: str,
    user_id: str,
    prompt: str,
    status: str = "running",
    interrupt_type: Optional[str] = None,
) -> None:
    query = """
    insert into public.blog_runs (thread_id, user_id, prompt, status, interrupt_type)
    values (%s, %s, %s, %s, %s)
    on conflict (thread_id) do nothing;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (thread_id, user_id, prompt, status, interrupt_type))

async def update_run_status(
    pool: AsyncConnectionPool,
    thread_id: str,
    status: str,
    interrupt_type: Optional[str] = None,
    error_message: Optional[str] = None,
    completed_at: Optional[datetime] = None,
) -> None:
    # Always update updated_at. Only set completed_at if provided.
    query = """
    update public.blog_runs
    set
      status = %s,
      interrupt_type = %s,
      error_message = %s,
      completed_at = coalesce(%s, completed_at),
      updated_at = now()
    where thread_id = %s;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (status, interrupt_type, error_message, completed_at, thread_id))

async def get_run(pool: AsyncConnectionPool, thread_id: str) -> Optional[Dict[str, Any]]:
    query = """
    select
      thread_id, user_id, prompt, status, interrupt_type, error_message,
      created_at, updated_at, completed_at
    from public.blog_runs
    where thread_id = %s
    limit 1;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (thread_id,))
            row = await cur.fetchone()

    if not row:
        return None

    keys = [
        "thread_id", "user_id", "prompt", "status", "interrupt_type", "error_message",
        "created_at", "updated_at", "completed_at",
    ]
    return dict(zip(keys, row))

async def list_runs_for_user(
    pool: AsyncConnectionPool,
    user_id: str,
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    query = """
    select
      thread_id, prompt, status, interrupt_type, created_at, completed_at
    from public.blog_runs
    where user_id = %s
    order by created_at desc
    limit %s offset %s;
    """
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (user_id, limit, offset))
            rows = await cur.fetchall()

    keys = ["thread_id", "prompt", "status", "interrupt_type", "created_at", "completed_at"]
    return [dict(zip(keys, r)) for r in rows]

def utc_now() -> datetime:
    return datetime.now(timezone.utc)
```

### `backend/db/crud/blog_outputs.py`

```python
from __future__ import annotations

import json
from typing import Any, Optional, Dict

from psycopg_pool import AsyncConnectionPool

async def save_output(
    pool: AsyncConnectionPool,
    thread_id: str,
    final_post_markdown: str,
    meta: Optional[Dict[str, Any]] = None,
) -> None:
    query = """
    insert into public.blog_outputs (thread_id, final_post_markdown, meta)
    values (%s, %s, %s::jsonb)
    on conflict (thread_id)
    do update set
      final_post_markdown = excluded.final_post_markdown,
      meta = excluded.meta;
    """
    meta_json = json.dumps(meta or {})
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(query, (thread_id, final_post_markdown, meta_json))

async def get_output(pool: AsyncConnectionPool, thread_id: str) -> Optional[Dict[str, Any]]:
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

    if not row:
        return None

    keys = ["thread_id", "final_post_markdown", "meta", "created_at"]
    return dict(zip(keys, row))
```

### `backend/db/crud/__init__.py`

```python
from .blog_runs import create_blog_run, update_run_status, get_run, list_runs_for_user
from .blog_outputs import save_output, get_output

__all__ = [
    "create_blog_run",
    "update_run_status",
    "get_run",
    "list_runs_for_user",
    "save_output",
    "get_output",
]
```

---

## 3) Wire this into your existing `main.py`

At the top, add:

```python
import uuid
from backend.db.crud import create_blog_run, update_run_status, save_output
from backend.db.crud.blog_runs import utc_now
```

Then inside `main()`:

### 3.1 Generate IDs and create run

Right before config:

```python
thread_id = str(uuid.uuid4())
user_id = "local-dev"  # replace later with real authenticated user id
prompt = "Write a blog post about the benefits of using MCP servers for Minecraft."

await create_blog_run(pool, thread_id=thread_id, user_id=user_id, prompt=prompt, status="running")
```

### 3.2 Use same thread_id for LangGraph

```python
config = {"configurable": {"thread_id": thread_id}, "run_name": "blog_writing_agent_run_25"}
initial_input = {"prompt": prompt}
```

### 3.3 When interrupted

After the first `astream(...)` loop finishes:

```python
await update_run_status(pool, thread_id, status="waiting_for_review", interrupt_type="image_review")
```

### 3.4 Before resume

```python
await update_run_status(pool, thread_id, status="running", interrupt_type=None)
```

### 3.5 After resume finishes: save output + mark complete

After the second `astream(None, ...)` finishes:

```python
state = await app.aget_state(config)
final_md = (
    state.values.get("final_post")
    or state.values.get("edited_draft")
    or state.values.get("draft")
    or ""
)

await save_output(
    pool,
    thread_id=thread_id,
    final_post_markdown=final_md,
    meta={
        "title": state.values.get("title"),
        "slug": state.values.get("slug"),
        "keywords_used": state.values.get("keywords_used"),
        "meta_description": state.values.get("meta_description"),
    },
)

await update_run_status(pool, thread_id, status="completed", completed_at=utc_now())
```

---

## 4) One more thing you must do: create the tables

If you haven’t run the Supabase SQL yet, your CRUD will fail. Use the table SQL I sent earlier (blog_runs + blog_outputs) first.

---

If you paste your Supabase `DATABASE_URL` format (mask the password) I can tell you whether you need `?sslmode=require` and whether your pool config needs any tweaks for Supabase.