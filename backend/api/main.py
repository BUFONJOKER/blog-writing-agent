import sys
import io
import asyncio
import uvicorn
from fastapi import FastAPI, status, HTTPException
from contextlib import asynccontextmanager
from api.schema.app_resources import AppResources
from api.schema.stream_manager import StreamManager
from psycopg_pool import AsyncConnectionPool
from agent.config import DB_URL
from langchain_ollama import ChatOllama
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agent.workflow import build_workflow
from agent.tools import initialize_tools
from fastapi.middleware.cors import CORSMiddleware
from api.routes.blog.main import blog_router
from api.routes.auth.main import auth_router
from api.config import OLLAMA_HOST
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # This ensures any library (like Psycopg) that checks the loop
    # during initialization gets the correct one.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


resources = AppResources()
stream_manager = StreamManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and tear down long-lived application resources.

    Args:
        app: FastAPI application instance receiving initialized resources.

    Returns:
        AsyncIterator[None]: Yields control to run the application lifecycle.
    """

    app.state.resources = resources
    app.state.stream_manager = stream_manager
    resources.pool = AsyncConnectionPool(
        conninfo=DB_URL,
        max_size=20,
        min_size=1,
        kwargs={"autocommit": True},
        open=False,  # Don't open immediately, we'll open it after the app starts
    )

    await resources.pool.open()  # Ensure the pool is ready before accepting requests

    resources.model = ChatOllama(model="qwen3.5:cloud", base_url=OLLAMA_HOST)

    checkpointer = AsyncPostgresSaver(resources.pool)

    resources.tools = await initialize_tools("hosted_horizon")

    resources.workflow = await build_workflow(
        checkpointer, resources.model, resources.tools
    )

    yield

    if resources.pool:
        await resources.pool.close()


app = FastAPI(title="Blog Writing Agent API", version="0.0.1", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # Must be specific, not "*"
    allow_credentials=True, # Required for Cookies
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Return a simple root response for quick API reachability checks.

    Args:
        None: This endpoint does not take request parameters.

    Returns:
        dict: A welcome message and a list of available endpoints for the Blog Writing Agent API.
    """

    return {
        "messages":"Hello from the Blog Writing Agent API",
        "endpoints": {
            "/health": "GET - Check health status of critical services",
            "/blog/generate": "POST - Start a new blog generation workflow",
            "/blog/review": "POST - Approve or reject a workflow at human-review step",
            "/blog/status": "GET - Check the status of an ongoing workflow by thread_id",
            "/blog/final_post":"POST - Retrieve the final blog post content after workflow completion by giving thread_id",
            "/blog/user_posts/{user_id}": "GET - Retrieve all blog outputs associated with a user_id",
        },
    }


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Report health status for critical runtime dependencies.

    Args:
        None: This endpoint does not take request parameters.

    Returns:
        dict: Healthy status payload when database, model, and workflow are ready.

    Raises:
        HTTPException: If one or more required services are unavailable.
    """

    is_db_up = resources.pool and not resources.pool.closed
    is_model_up = resources.model is not None
    is_workflow_up = resources.workflow is not None

    if all([is_db_up, is_model_up, is_workflow_up]):
        return {"status": "healthy", "database": "ok", "ollama": "ok", "workflow": "ok"}

    raise HTTPException(status_code=503, detail="Service Degraded")


app.include_router(blog_router)
app.include_router(auth_router)

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
