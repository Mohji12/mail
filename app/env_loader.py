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


def _normalize_origin(url: str) -> str:
    return (url or "").strip().rstrip("/")


def cors_origins() -> list[str]:
    """Allowed browser origins. CORS_ORIGINS env can add comma-separated URLs or *."""
    defaults = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8001",
        "http://localhost:8001",
        # Vercel frontend — https://mail-iota-lilac.vercel.app/
        "https://mail-iota-lilac.vercel.app",
        "https://staging.d5w312h4wy6nw.amplifyapp.com",
        "https://d5w312h4wy6nw.amplifyapp.com",
        "https://staging.d1daw2yg43xlwa.amplifyapp.com",
        "https://d1daw2yg43xlwa.amplifyapp.com",
        "https://diazstudios.site",
        "https://cedat.menteetracker.com",
        "https://mail.harishcriticalcareclasses.com",
        "https://www.harishcriticalcareclasses.com",
        "https://harishcriticalcareclasses.com",
    ]
    defaults = [_normalize_origin(o) for o in defaults]
    extra = os.getenv("CORS_ORIGINS", "").strip()
    if extra == "*":
        return ["*"]
    if extra:
        merged = defaults + [
            _normalize_origin(o) for o in extra.split(",") if o.strip()
        ]
        return list(dict.fromkeys(merged))
    return defaults


def cors_allow_all() -> bool:
    return os.getenv("CORS_ALLOW_ALL", "").strip().lower() in ("1", "true", "yes", "on")


def cors_origin_regex() -> str | None:
    """
    Regex for extra allowed origins (e.g. all Vercel preview URLs).
    Set CORS_ORIGIN_REGEX=... to override; set CORS_VERCEL=false to disable Vercel pattern.
    """
    custom = os.getenv("CORS_ORIGIN_REGEX", "").strip()
    if custom:
        return custom
    if os.getenv("CORS_VERCEL", "true").strip().lower() in ("0", "false", "no", "off"):
        return None
    return r"https://[a-z0-9][a-z0-9-]*\.vercel\.app"
