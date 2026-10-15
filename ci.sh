#!/bin/bash
# Run locally what a push must survive: the migration tests on an ephemeral
# TimescaleDB (needs Docker). Usage: ./ci.sh
set -euo pipefail

step() { printf '\n=== %s ===\n' "$1"; shift; "$@"; }

step "uv sync (locked)" uv sync --all-groups --locked

if ! docker info >/dev/null 2>&1; then
  echo "ERROR: docker is not running — the test suite uses testcontainers." >&2
  exit 1
fi
step "tests" uv run pytest -q

printf '\nAll CI checks passed.\n'
