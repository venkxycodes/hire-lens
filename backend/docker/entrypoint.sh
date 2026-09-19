#!/usr/bin/env bash
set -euo pipefail

ROLE="${SERVICE_ROLE:-api}"
DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-host.settings.base}"

export DJANGO_SETTINGS_MODULE

case "$ROLE" in
  migrate)
    exec python manage.py migrate --noinput
    ;;
  api)
    exec gunicorn host.wsgi:application \
      --bind "0.0.0.0:${PORT:-8000}" \
      --workers "${GUNICORN_WORKERS:-2}" \
      --threads "${GUNICORN_THREADS:-4}" \
      --timeout "${GUNICORN_TIMEOUT:-120}"
    ;;
  async)
    exec uvicorn host.asgi:application \
      --host "0.0.0.0" \
      --port "${PORT:-8001}" \
      --workers "${UVICORN_WORKERS:-1}"
    ;;
  worker)
    exec python manage.py run_worker --name "${WORKER_NAME:-default}"
    ;;
  *)
    echo "Unknown SERVICE_ROLE: $ROLE (expected migrate, api, async, or worker)" >&2
    exit 1
    ;;
esac
