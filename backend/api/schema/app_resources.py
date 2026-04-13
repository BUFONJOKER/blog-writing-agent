from pydantic import BaseModel, ConfigDict, Field
from typing import Any
from psycopg_pool import AsyncConnectionPool


class AppResources(BaseModel):
    """Container for shared application resources used across the backend.

    This model groups long-lived objects such as the database pool, loaded
    model instances, workflow graphs, and tool clients so they can be passed
    around in a structured way during application startup and request handling.
    """
    prompt: str = Field(
        default="",
        description="The initial prompt for the blog generation workflow, set at request time.",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    pool: AsyncConnectionPool = Field(
        default=None,
        description="Async PostgreSQL connection pool shared by backend services.",
    )

    model: Any = Field(
        default=None,
        description="Shared model instance used by agent or API components.",
    )

    workflow: Any = Field(
        default=None,
        description="Shared workflow or graph object for orchestration logic.",
    )

    tools: Any = Field(
        default=None,
        description="Shared tool collection or client wrapper used by the app.",
    )

    run_name: str = Field(
        default="",
        description="Run name for langsmith tracing"
    )
