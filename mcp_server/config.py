import os
from pathlib import Path
from dotenv import load_dotenv

# Find the project root by looking for the parent of the current folder
# This goes up one level from 'backend/' or 'mcp_server/' to the main project folder
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"

# Load the file specifically from the root
load_dotenv(dotenv_path=env_path)

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db") # With default value
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    @classmethod
    def validate(cls):
        """Ensure critical vars are present"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in the .env file")

# Validate on import
Config.validate()