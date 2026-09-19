import os
from pathlib import Path


def load_dotenv() -> None:
    """Load a local .env file when present (no-op in production)."""
    env_file = Path(__file__).resolve().parents[2] / ".env"
    if not env_file.is_file():
        return
    try:
        from dotenv import load_dotenv as _load
    except ImportError:
        return
    _load(env_file, override=False)


def get_default_settings_module() -> str:
    """Return the default settings module for the current runtime."""
    existing = os.environ.get("DJANGO_SETTINGS_MODULE")
    if existing:
        return existing

    env = (os.environ.get("ENV") or "local").strip().lower()
    if env in {"test", "testing"}:
        return "host.settings.test"
    if env in {"prod", "production"}:
        return "host.settings.base"
    return "host.settings.local"


def configure_default_settings_module() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", get_default_settings_module())
    if os.environ["DJANGO_SETTINGS_MODULE"] == "host.settings.local":
        load_dotenv()
