#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p data/local
if [[ ! -f .env ]]; then
  cp .env.example .env
fi
export PYTHONPATH="$ROOT/backend"
"$ROOT/.venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 8765
