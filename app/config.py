import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return val


INSTAGRAM_VERIFY_TOKEN: str = _require("INSTAGRAM_VERIFY_TOKEN")
INSTAGRAM_PAGE_ACCESS_TOKEN: str = _require("INSTAGRAM_PAGE_ACCESS_TOKEN")
INSTAGRAM_APP_SECRET: str = _require("INSTAGRAM_APP_SECRET")

ANTHROPIC_API_KEY: str = _require("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")

REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "small")

RATE_LIMIT_MAX: int = int(os.getenv("RATE_LIMIT_MAX", "5"))
RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "3600"))

# Instagram Graph API base URL
GRAPH_API_URL: str = "https://graph.facebook.com/v21.0"
