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
    return current.parent # Fallback

# Global Constants
BASE_DIR = get_project_root()
ENV_PATH = BASE_DIR / ".env"

# Load the environment variables
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv() # Fallback for Docker/Prod

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")