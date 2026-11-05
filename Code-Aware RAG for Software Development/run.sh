#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python 3 is required. Install Python 3.10 or newer and try again."
  exit 1
fi
"$PYTHON" -m pip install --user -r requirements.txt
exec "$PYTHON" app.py
