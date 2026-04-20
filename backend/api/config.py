import os
from pathlib import Path
from dotenv import load_dotenv


def get_project_root() -> Path:
    """Locate the backend project root directory.

    Args:
        None: The lookup is based on the current file location.

    Returns:
        Path: The nearest parent directory containing project markers such as
        `.env` or `pyproject.toml`.
    """
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

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
OLLAMA_HOST = os.getenv("OLLAMA_HOST")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OLLAMA_REMOTE_URL = os.getenv("OLLAMA_REMOTE_URL")
