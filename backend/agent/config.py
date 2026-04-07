import os
from pathlib import Path
from dotenv import load_dotenv


def get_project_root() -> Path:
    """Climbs up from the current file to find the project root."""
    current = Path(__file__).resolve()
    # Look for a marker that only exists in your root directory
    for parent in current.parents:
        if (parent / ".env").exists() or (parent / "pyproject.toml").exists():
            return parent
    return current.parent  # Fallback


# Global Constants
BASE_DIR = get_project_root()
ENV_PATH = BASE_DIR / ".env"

# Load the environment variables
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()  # Fallback for Docker/Prod

HORIZON_TOKEN = os.getenv("HORIZON_TOKEN")
DB_URL = os.getenv("DB_URL")
DB_POOLER_URL = os.getenv("DB_POOLER_URL")
HUGGINGFACEHUB_API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
