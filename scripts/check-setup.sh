#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "Repo root: $ROOT"
echo "Python:    $(command -v python3 || echo MISSING)"
python3 --version 2>/dev/null || true
echo "Venv:      $([ -x .venv/bin/python ] && echo OK || echo MISSING — create with python3 -m venv .venv)"
echo "Uvicorn:   $([ -x .venv/bin/python ] && .venv/bin/python -c 'import uvicorn; print(uvicorn.__version__)' 2>/dev/null || echo MISSING — pip install -r backend/requirements.txt)"
echo "Node:      $(command -v node || echo MISSING — install Node 20+)"
echo "npm:       $(command -v npm || echo MISSING — same as Node)"
echo ".env:      $([ -f .env ] && echo OK || echo MISSING — cp .env.example .env)"
