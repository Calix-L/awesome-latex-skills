#!/usr/bin/env bash
# Compatibility entrypoint; portable tests also run directly with Python.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ "$#" -ne 0 ]; then
    echo "Usage: bash tests/run_tests.sh (filter with python -m unittest)" >&2
    exit 2
fi
cd "$ROOT"
if command -v python3 >/dev/null 2>&1 && python3 -c 'import sys; assert sys.version_info >= (3, 10)' >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1 && python -c 'import sys; assert sys.version_info >= (3, 10)' >/dev/null 2>&1; then
    PYTHON=python
else
    echo "Python 3.10+ was not found. Install it and requirements-dev.txt first." >&2
    exit 1
fi
"$PYTHON" scripts/validate_repo.py
"$PYTHON" -m unittest discover -s tests -v
