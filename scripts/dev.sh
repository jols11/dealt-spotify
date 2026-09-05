#!/usr/bin/env bash
# Start API + UI together. Leave this terminal open.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p data/local
if [[ ! -f .env ]]; then
  cp .env.example .env
fi
if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  python3 -m venv "$ROOT/.venv"
  "$ROOT/.venv/bin/python" -m pip install -r "$ROOT/backend/requirements.txt"
fi
if [[ ! -d "$ROOT/frontend/node_modules" ]]; then
  (cd "$ROOT/frontend" && npm install)
fi

cleanup() {
  kill "${API_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT

export PYTHONPATH="$ROOT/backend"
"$ROOT/.venv/bin/python" -m uvicorn app.main:app --host 127.0.0.1 --port 8765 &
API_PID=$!
sleep 1
if ! curl -sf http://127.0.0.1:8765/api/health >/dev/null; then
  echo "API failed to start on 8765." >&2
  exit 1
fi
echo "API http://127.0.0.1:8765   UI http://127.0.0.1:4177"
cd "$ROOT/frontend"
npm run dev -- --host 127.0.0.1 --port 4177
