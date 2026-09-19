import os

from .base import *  # noqa: F403


ENV = os.environ.get("ENV", "local")
SETTINGS_PROFILE = "local"
DEBUG = True
ALLOWED_HOSTS = ["*"]

if not os.environ.get("DATABASE_URL") and not os.environ.get("POSTGRES_HOST"):
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3", "OPTIONS": {"timeout": 20}}}
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "testserver"]

CSRF_TRUSTED_ORIGINS = ["http://127.0.0.1:5188", "http://localhost:5188"]
