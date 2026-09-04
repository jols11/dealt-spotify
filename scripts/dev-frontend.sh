#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"
npm run dev -- --host 127.0.0.1 --port 4177
