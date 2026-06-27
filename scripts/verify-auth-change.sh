#!/usr/bin/env bash
set -euo pipefail

uv run --extra dev python -m pytest tests/test_auth.py tests/test_server.py -q
uv run --extra dev ruff check lc_agent tests

(
  cd frontend
  npm run test:auth
  npm run build
)
