import os
from pathlib import Path

from dotenv import load_dotenv

_APP_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _APP_DIR.parent


def load_app_env() -> None:
    """Load .env from project root and app/ (app/.env wins)."""
    load_dotenv(_PROJECT_ROOT / ".env")
    load_dotenv(_APP_DIR / ".env", override=True)


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value or not str(value).strip():
        raise RuntimeError(
            f"Missing {name}. Set it in app/.env (local) or as a host environment variable (production)."
        )
    return value.strip()
