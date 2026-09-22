import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parents[2]

ENV = (os.environ.get("ENV") or "local").strip().lower()
SETTINGS_PROFILE = "base"
DEBUG = False
APP_VERSION = os.environ.get("APP_VERSION", "0.1.0")

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-change-me")
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "recruiting",
    "rest_framework",
    "graphene_django",
    "api.apps.ApiConfig",
    "workers.apps.WorkersConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
]

ROOT_URLCONF = "host.urls"
WSGI_APPLICATION = "host.wsgi.application"
ASGI_APPLICATION = "host.asgi.application"


def _build_databases():
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        parsed = urlparse(database_url)
        return {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": parsed.path.lstrip("/"),
                "USER": parsed.username or "",
                "PASSWORD": parsed.password or "",
                "HOST": parsed.hostname or "localhost",
                "PORT": str(parsed.port or 5432),
            }
        }
    return {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "app"),
            "USER": os.environ.get("POSTGRES_USER", "app"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "app"),
            "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        }
    }


DATABASES = _build_databases()

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

GRAPHENE = {
    "SCHEMA": "api.graphql.schema.schema",
}

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.environ.get("LOG_LEVEL", "INFO")},
}

MEDIA_ROOT = BASE_DIR / "media"
DATA_UPLOAD_MAX_MEMORY_SIZE = 110 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FILES = 20
JEV_MODE = os.environ.get("JEV_MODE", "live")
JEV_API_KEY = os.environ.get("JEV_API_KEY", "")
JEV_MODEL = os.environ.get("JEV_MODEL", "jev-1.13.0")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "google/gemma-4-26b-a4b-it:free")
OPENROUTER_MODELS = [item.strip() for item in os.environ.get("OPENROUTER_MODELS", "google/gemma-4-26b-a4b-it:free,google/gemma-4-31b-it:free,openrouter/free,nvidia/nemotron-3-ultra:free,nvidia/nemotron-3-super:free,inclusionai/ling-3.0-flash-vl:free,dots-studio/dots-3-note-preview:free,nvidia/nemotron-3.5-lightning:free,nex-agi/nex-n2.5-mini:free,openai/gpt-oss-120b:free").split(",") if item.strip()]
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
if ENV in {"production", "prod"}:
    if SECRET_KEY == "dev-insecure-change-me":
        raise ValueError("Set a strong SECRET_KEY for production")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
SESSION_COOKIE_NAME = "hirelens_session"
CSRF_COOKIE_NAME = "hirelens_csrf"
