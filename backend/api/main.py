import sys
import io
import asyncio
import uvicorn
from fastapi import FastAPI, status, HTTPException
from contextlib import asynccontextmanager
from api.schema.app_resources import AppResources
from psycopg_pool import AsyncConnectionPool
from agent.config import DB_URL
from langchain_ollama import ChatOllama
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agent.workflow import build_workflow
from agent.tools import initialize_tools
from fastapi.middleware.cors import CORSMiddleware
from api.routes.blog import blog_router


if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # This ensures any library (like Psycopg) that checks the loop
    # during initialization gets the correct one.
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


resources = AppResources()

@asynccontextmanager
async def lifespan(app: FastAPI):

    resources.pool = AsyncConnectionPool(
        conninfo=DB_URL,
        max_size=20,
        min_size=1,
        kwargs={"autocommit": True},
    )

    resources.model = ChatOllama(model="qwen3.5:cloud")

    checkpointer = AsyncPostgresSaver(resources.pool)

    resources.tools = await initialize_tools("hosted")

    resources.workflow = await build_workflow(checkpointer, resources.model, resources.tools)

    yield

    if resources.pool:
        await resources.pool.close()

app = FastAPI(title='Blog Writing Agent API', version="0.0.1", lifespan=lifespan)


app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"http://localhost:3000",   # Next.js dev
		# "https://your-vercel-domain.vercel.app",
		# "https://your-custom-domain.com",
	],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


@app.get("/")
def root():
    return {"hello": "world"}

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Checks if DB, Ollama, and Agent are initialized."""
    is_db_up = resources.pool and not resources.pool.closed
    is_model_up = resources.model is not None
    is_workflow_up = resources.workflow is not None

    if all([is_db_up, is_model_up, is_workflow_up]):
        return {"status": "healthy", "database": "ok", "ollama": "ok", "workflow": "ok"}

    raise HTTPException(status_code=503, detail="Service Degraded")

app.include_router(blog_router)

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)