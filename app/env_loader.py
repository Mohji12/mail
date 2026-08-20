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


def cors_origins() -> list[str]:
    """Allowed browser origins. CORS_ORIGINS env can add comma-separated URLs or *."""
    defaults = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8001",
        "http://localhost:8001",
        "https://staging.d5w312h4wy6nw.amplifyapp.com",
        "https://d5w312h4wy6nw.amplifyapp.com",
        "https://diazstudios.site",
        "https://cedat.menteetracker.com",
    ]
    extra = os.getenv("CORS_ORIGINS", "").strip()
    if extra == "*":
        return ["*"]
    if extra:
        merged = defaults + [o.strip() for o in extra.split(",") if o.strip()]
        return list(dict.fromkeys(merged))
    return defaults
