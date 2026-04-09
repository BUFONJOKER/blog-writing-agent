Perfect — your `BlogAgentState` already tells us exactly what to persist:

- **Run record** fields map to: `thread_id`, `prompt`, `status`, `interrupt_type`, `error`, `created_at`, `completed_at`, `user_id`
- **Final output** should be saved from: `final_post` (best)

    (If `final_post` is ever empty, fallback to `edited_draft` or `draft`.)


Below is the concrete step-by-step guide (with exact “where to change what”) for your current `main.py` + Supabase + AsyncPostgresSaver setup, while keeping *all DB code in `backend/db/`*.

---

## 1) Create tables in Supabase (SQL editor)

Run this in Supabase SQL editor (recommended first milestone):

```sql
create table if not exists public.blog_runs (
  id uuid primary key default gen_random_uuid(),
  thread_id text not null unique,
  user_id text not null,
  prompt text not null,
  status text not null,
  interrupt_type text,
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz
);

create index if not exists idx_blog_runs_user_created
  on public.blog_runs (user_id, created_at desc);

create table if not exists public.blog_outputs (
  id uuid primary key default gen_random_uuid(),
  thread_id text not null unique references public.blog_runs(thread_id) on delete cascade,
  final_post_markdown text not null,
  meta jsonb,
  created_at timestamptz not null default now()
);
```

This satisfies “tables exist after migration”.

---

## 2) Add DB CRUD code under `backend/db/`

Create these files:

```
backend/db/
  __init__.py
  crud/
    __init__.py
    blog_runs.py
    blog_outputs.py
```

### 2.1 `backend/db/crud/blog_runs.py` (async SQL with your pool)

Use `psycopg_pool.AsyncConnectionPool` exactly like your checkpointer does.

Implement:

- `create_blog_run(pool, thread_id, user_id, prompt, status="running", interrupt_type=None)`
- `update_run_status(pool, thread_id, status, interrupt_type=None, error_message=None, completed_at=None)`
- `get_run(pool, thread_id)`
- `list_runs_for_user(pool, user_id, limit=50, offset=0)` (ORDER BY created_at DESC)

**Important detail:** use parameterized queries (`%s`) to avoid SQL injection.

### 2.2 `backend/db/crud/blog_outputs.py`

Implement:

- `save_output(pool, thread_id, final_post_markdown, meta=None)`

Use upsert:

```sql
insert into public.blog_outputs (thread_id, final_post_markdown, meta)
values (%s, %s, %s)
on conflict (thread_id)
do update set final_post_markdown = excluded.final_post_markdown,
              meta = excluded.meta;
```

---

## 3) Update `main.py` to create/update DB records around the run

Your `main.py` is the perfect place to start integrating persistence (even before FastAPI endpoints).

### 3.1 Generate a real thread_id

Replace your hardcoded thread id:

```python
{"thread_id": "19_final_blog_test_with_images"}
```

with:

```python
import uuid
thread_id = str(uuid.uuid4())
```

### 3.2 Add a placeholder user_id (for now)

Until auth is wired, do:

```python
user_id = "local-dev"
```

### 3.3 Create BlogRun BEFORE starting graph

Right before the first `app.astream(...)`:

- `await create_blog_run(pool, thread_id, user_id, prompt, status="running")`

### 3.4 Set config using the SAME thread_id

```python
config = {
  "configurable": {"thread_id": thread_id},
  "run_name": f"blog_writing_agent_run_{thread_id[:8]}"
}
```

### 3.5 When the graph interrupts, update status + interrupt_type

After the first stream finishes, do:

- `await update_run_status(pool, thread_id, status="waiting_for_review", interrupt_type="plan_review")`

But note: **your interrupt is after `image_generation_node`** right now. So your interrupt type should match reality, e.g.:

- `interrupt_type="image_review"` (or `"post_image_generation_review"`)

If your intention is truly “plan review”, move the interrupt point (see Step 4).

### 3.6 On resume start, set running again

Right before resuming:

- `await update_run_status(pool, thread_id, status="running", interrupt_type=None)`

### 3.7 After completion, save output + mark completed

After the second `astream(None, ...)` finishes:

1) Fetch state:

```python
state = await app.aget_state(config)
```

2) Choose final markdown:

- primary: `state.values.get("final_post")`
- fallback: `edited_draft` then `draft`

3) Save output:

```python
await save_output(pool, thread_id, final_post_markdown, meta={"title": state.values.get("title"), "slug": state.values.get("slug")})
```

4) Mark run done:

```python
await update_run_status(pool, thread_id, status="completed", completed_at=<now>)
```

(Use `datetime.now(timezone.utc)` for `completed_at`.)

This satisfies:

- CRUD works (create/update/read/list)
- output saved
- status lifecycle tracked

---

## 4) Fix the “plan review” mismatch (optional but recommended)

In `workflow.py` you compile with:

```python
workflow = graph.compile(checkpointer=checkpointer, interrupt_after=['image_generation_node'])
```

But in `main.py` you comment:

> GRAPH IS NOW INTERRUPTED AFTER IMAGE_GENERATION_NODE
>

> Fetch the state to show the human the plan
>

That’s inconsistent: the plan is produced earlier (`planner_node`). If you want the human to review the plan before writing, change to:

```python
workflow = graph.compile(checkpointer=checkpointer, interrupt_after=['planner_node'])
```

Or if you want two human gates:

- interrupt after `planner_node` (plan approval)
- and later after `critic_node` (final approval)

…that’s doable, but start with one.

---

## 5) What you should persist from your BlogAgentState (mapping)

### BlogRun columns

- `thread_id` ← from generated uuid (also config thread_id)
- `user_id` ← placeholder now, real user later
- `prompt` ← `initial_input["prompt"]`
- `status` ← your DB lifecycle (`running`, `waiting_for_review`, `completed`, `failed`)
- `interrupt_type` ← match your interrupt location (`plan_review`, `final_review`, `image_review`)
- `error_message` ← from `state.values.get("error")` or exception handling
- `completed_at` ← when finished

### BlogOutput columns

- `final_post_markdown` ← `state.values["final_post"]`
- `meta` ← `title`, `slug`, `keywords_used`, `meta_description`, maybe `image_plan`

---

## 6) Listing runs (reverse chronological)

Once you have data, your function:

`list_runs_for_user(pool, user_id)` should run:

```sql
select thread_id, prompt, status, interrupt_type, created_at, completed_at
from public.blog_runs
where user_id = %s
order by created_at desc
limit %s offset %s;
```

This satisfies the “reverse chronological order” acceptance criterion.

---

If you want, paste your existing `backend/db/__init__.py` (and whether you already have any DB code there). I can then give you the exact code blocks for `backend/db/crud/blog_runs.py` and `backend/db/crud/blog_outputs.py` that match your `AsyncConnectionPool` usage and Supabase SSL requirements.