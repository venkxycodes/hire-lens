#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
pids=()
cleanup() {
  for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done
}
trap cleanup EXIT
trap 'exit 130' INT TERM
(cd "$project_dir/backend" && exec .venv/bin/python manage.py runserver 127.0.0.1:8018 --noreload) &
pids+=("$!")
(cd "$project_dir/backend" && exec .venv/bin/python manage.py run_worker) &
pids+=("$!")
(cd "$project_dir/frontend" && exec npm run dev) &
pids+=("$!")
echo 'Jack & Jill: http://127.0.0.1:5188 — stop with Ctrl+C'
wait
