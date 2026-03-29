import os
from pathlib import Path
from dotenv import load_dotenv

# 1. Setup paths for local development
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"

# 2. Load .env ONLY if it exists (Local WSL logic)
# In Docker, this will simply skip if you didn't copy the .env into the image.
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    # Fallback to standard loading for Docker/Production environments
    load_dotenv()

class Config:
    # 3. Access variables (Works for both .env and Docker -e flags)
    HORIZON_TOKEN = os.getenv("HORIZON_TOKEN")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    @classmethod
    def validate(cls):
        """Ensure critical vars are present"""
        if not cls.HORIZON_TOKEN:
            # Provide a more helpful error for Docker users
            raise ValueError(
                "HORIZON_TOKEN is missing. "
                "Ensure it is in your .env or passed via 'docker run -e'."
            )

# Validate on import
Config.validate()