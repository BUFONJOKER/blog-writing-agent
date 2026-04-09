Here are **all Phase 4 (FastAPI)** tasks in your Tasks Board, explained in a clear “what you’re building + what to implement + what to verify” way.

---

## 4.1 — Create the FastAPI app [[1]](https://www.notion.so/4-1-Create-the-FastAPI-app-32fc1cfa959c811bba9fcca12da38c16?pvs=21)

**Goal:** Stand up the FastAPI server that will host all API routes and initialize resources on startup.

**Implement**

- Create `api/main.py` and the `FastAPI()` app (title/version).
- Add a **lifespan** startup/shutdown handler (init DB/graph/tool clients; close them on shutdown).
- Add **CORS middleware** (allow your frontend origin).
- Add `GET /health`.
- Create `api/routes/blog.py` + `api/routes/auth.py` and include routers (`/blog`, `/auth`).
- Run with **uvicorn on port 8000**; verify `/docs`.

**Verify**

- `/health` returns 200
- `/docs` loads
- CORS headers are present
- lifespan runs

[[1]](https://www.notion.so/4-1-Create-the-FastAPI-app-32fc1cfa959c811bba9fcca12da38c16?pvs=21)

---

## 4.2 — Build the `/blog/start` endpoint [[2]](https://www.notion.so/4-2-Build-the-blog-start-endpoint-32fc1cfa959c81149088d4d6d6a85a2e?pvs=21)

**Goal:** Start a new blog generation run *without blocking* the HTTP response.

**Implement**

- In `api/routes/blog.py`:
    - Request model: `prompt`, `user_id`, optional `tone`, `target_audience`.
    - `POST /blog/start`:
        - generate a `thread_id`
        - create a DB record with status `running`
        - build initial graph state
        - kick off the LangGraph run in a **background task**
        - return immediately: `{thread_id, status: "running"}`
- Background function:
    - runs graph with `thread_id`
    - updates DB status to `awaiting_human`, `complete`, or `error`

**Verify**

- Response returns immediately (no waiting)
- background errors don’t crash server
- DB record exists and status updates correctly

---

## 4.3 — Build the `/blog/{thread_id}/status` endpoint [[3]](https://www.notion.so/4-3-Build-the-blog-thread_id-status-endpoint-32fc1cfa959c813db609f92a7f2dd9dc?pvs=21)

**Goal:** Let the frontend poll and decide what UI to show (progress vs review vs results).

**Implement**

- `GET /blog/{thread_id}/status`
- Load DB run record (404 if missing)
- Load graph/checkpointer state (by `thread_id`)
- Return:
    - `status`: `running | awaiting_human | complete | error`
    - `current_node` (if you track it)
    - `awaiting_human` boolean
    - `interrupt_type` (plan review vs final review)
    - plus timestamps
- If awaiting plan review: include plan + task list
- If awaiting final review: include current draft

**Verify**

- Correct statuses
- Correct `interrupt_type`
- 404 for unknown IDs

---

## 4.4 — Build the `/blog/{thread_id}/review` endpoint [[4]](https://www.notion.so/4-4-Build-the-blog-thread_id-review-endpoint-32fc1cfa959c81bd82f9f4030ea3e59a?pvs=21)

**Goal:** Human-in-the-loop (HIL) endpoint to **resume** a paused graph after user approves/edits/rejects.

**Implement**

- Request supports actions: `approve | edit | reject`
- Validate:
    - run exists
    - run is **awaiting human input** (otherwise 400)
- Apply the human decision into graph state:
    - approve: mark approved
    - edit: replace plan/draft with edited version + feedback
    - reject: attach feedback and route back (regenerate / rewrite)
- Resume graph in a **background task**
- Update DB status back to `running`

**Verify**

- Approve/edit/reject all resume correctly
- 400 if not awaiting review
- status transitions make sense

---

## 4.5 — Build the `/blog/{thread_id}/result` endpoint [[5]](https://www.notion.so/4-5-Build-the-blog-thread_id-result-endpoint-32fc1cfa959c81b6916ccc5844a835e3?pvs=21)

**Goal:** Return the final blog post once the run is complete.

**Implement**

- `GET /blog/{thread_id}/result`
- 404 if run not found
- 400 if run not complete
- Return:
    - `final_post` (markdown)
    - metadata
    - word_count
    - completed_at

**Verify**

- Works only when complete
- error responses are clear

---

## 4.6 — Add SSE for real-time streaming [[6]](https://www.notion.so/4-6-Add-SSE-for-real-time-streaming-32fc1cfa959c81d5b68aeb36d2511685?pvs=21)

**Goal:** Push live progress to frontend (node start/finish, tool calls, etc.) without polling.

**Implement**

- `GET /blog/{thread_id}/stream` using **Server-Sent Events**
- Stream events while run is active
- If graph pauses for review: emit `awaiting_human` event, then stop/close stream
- Close cleanly on completion/error/client disconnect

**Verify**

- Stream stays open during execution
- Disconnects don’t leak resources
- frontend receives meaningful events

---

## 4.7 — Add authentication middleware [[7]](https://www.notion.so/4-7-Add-authentication-middleware-32fc1cfa959c81568533dead32810d23?pvs=21)

**Goal:** Protect blog endpoints so only logged-in users can start/see their runs.

**Implement**

- Add JWT + password hashing dependencies
- In `api/routes/auth.py`:
    - token endpoint (email/password → `{access_token, token_type}`)
- Create auth helpers (create/verify JWT)
- Add dependency/middleware so blog routes require a valid token
- JWT includes user identity (user id/email) and has expiry (e.g., 24h)

**Verify**

- No token → 401
- Valid token → success
- token expiry enforced

---

## 4.8 — Add database models and migrations [[8]](https://www.notion.so/4-8-Add-database-models-and-migrations-32fc1cfa959c8104a60ada2f407c4cb9?pvs=21)

**Goal:** Create real DB schema (SQLAlchemy + Alembic) for users and blog runs/outputs.

**Implement**

- `db/models.py`: `User`, `BlogRun`, `BlogOutput` (and relationships)
- `db/session.py`: async engine + session
- `alembic init alembic`
- Configure Alembic to use `Base.metadata`
- Autogenerate + run initial migration
- Ensure indexes/FKs (esp. `thread_id`, `user_id`)

**Verify**

- Tables exist after `alembic upgrade head`
- FK constraints correct
- autogenerate works (second migration empty)

---

## 4.9 — Persist generated blog posts (runs, sections, final markdown, metadata) [[9]](https://www.notion.so/4-9-Persist-generated-blog-posts-runs-sections-final-markdown-metadata-54d718007cae41d19121ad5d758245b7?pvs=21)

This task page is empty right now, but based on the title it means:

**Goal:** Store everything the agent produces so results can be retrieved later (and not only from in-memory graph state).

**Implement (typical breakdown)**

- Persist:
    - run record: prompt, user_id, status, created/completed times
    - intermediate artifacts: outline/plan, sections, tool sources
    - final markdown + metadata (tone, audience, keywords, word count, etc.)
- Update DB continuously (or at checkpoints) during graph execution
- Ensure your `/status` and `/result` read from DB (with fallback to graph state only if needed)

**Verify**

- restart server and you can still fetch old results
- “complete” runs always have final markdown stored

---

## 4.10 — API to list past blogs + get blog by id [[10]](https://www.notion.so/4-10-Add-API-list-past-blogs-get-blog-by-id-load-past-runs-755e56a65a3a4768be8e069a892d0a24?pvs=21)

Also empty page, but the title implies:

**Goal:** Build endpoints for “History” UI.

**Implement**

- `GET /blog` (or `/blog/runs`) to list runs for the current user (paginated)
- `GET /blog/{thread_id}` (or run id) to fetch one saved run + output

**Verify**

- returns only the authenticated user’s data
- pagination/sorting works (newest first)

---

## 4.11 — Store image assets (URLs + attribution) and link to blog post [[11]](https://www.notion.so/4-11-Add-storage-for-image-assets-URLs-attribution-and-link-to-blog-post-893eb57b0c5f410ab0a5c9fa677330a4?pvs=21)

Also empty page, but the title implies:

**Goal:** When you fetch/generate images, persist the asset metadata and associate it with a blog post.

**Implement**

- DB table/model like `ImageAsset`:
    - url
    - source (pexels/unsplash/etc.)
    - attribution fields (author, license, source_page_url)
    - alt text / caption
    - blog_run_id/thread_id FK
- Update blog output to reference images (hero image, inline images)

**Verify**

- retrieving a blog also returns its images + attribution
- attribution is never lost

---

If you want, I can summarize the **recommended implementation order** for these (what to build first so everything compiles and tests cleanly).