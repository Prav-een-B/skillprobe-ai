"""
Application configuration — loads settings from environment variables.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    MAX_QUESTIONS_PER_SKILL: int = 3
    SESSION_TIMEOUT_MINUTES: int = 60


settings = Settings()
