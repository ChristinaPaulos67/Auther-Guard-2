import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "auther-guard-dev-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'auther_guard.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEMO_MODE = os.environ.get("DEMO_MODE", "true").lower() in ("1", "true", "yes")
    DATA_DIR = BASE_DIR / "data"
    UPLOAD_FOLDER = BASE_DIR / "data" / "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    XAI_API_KEY = os.environ.get("XAI_API_KEY", "")


config_by_name = {
    "development": Config,
    "production": Config,
    "default": Config,
}
