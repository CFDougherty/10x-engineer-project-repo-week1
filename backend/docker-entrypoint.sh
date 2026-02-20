#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8000}"

if [ "$#" -eq 0 ]; then
  set -- uvicorn main:app --host 0.0.0.0 --port "$PORT"
fi

exec "$@"
