"""Runtime configuration - all from environment variables (see .env.example)."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    return default if v is None else v.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    model: str = os.getenv("KAAMYA_MODEL", "claude-sonnet-5-5")
    max_tokens: int = int(os.getenv("KAAMYA_MAX_TOKENS", "1500"))
    api_key: str = os.getenv("KAAMYA_API_KEY", "")            # app backend -> this service
    admin_key: str = os.getenv("KAAMYA_ADMIN_KEY", "")        # admin console / pandit review
    db_path: str = os.getenv("KAAMYA_DB_PATH", "kaamya_muhurtha.db")
    auto_approve: bool = _bool("KAAMYA_AUTO_APPROVE", False)  # False = pandit must approve (beta)
    session_ttl_hours: int = int(os.getenv("KAAMYA_SESSION_TTL_HOURS", "48"))
    result_ttl_days: int = int(os.getenv("KAAMYA_RESULT_TTL_DAYS", "30"))
    webhook_url: str = os.getenv("KAAMYA_WEBHOOK_URL", "")
    webhook_secret: str = os.getenv("KAAMYA_WEBHOOK_SECRET", "")
    review_promise_hours: int = int(os.getenv("KAAMYA_REVIEW_PROMISE_HOURS", "24"))
    assistant_name: str = os.getenv("KAAMYA_ASSISTANT_NAME", "Kaamya Acharya")
    default_city: str = os.getenv("KAAMYA_DEFAULT_CITY", "Hyderabad")
    max_window_days: int = int(os.getenv("KAAMYA_MAX_WINDOW_DAYS", "366"))


settings = Settings()
