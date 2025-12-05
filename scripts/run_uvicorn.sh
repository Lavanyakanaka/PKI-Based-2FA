#!/usr/bin/env bash
set -e
# Ensure PYTHONPATH includes vendor packages installed in image
export PYTHONPATH="${PYTHONPATH:-/srv/app/vendor}"
exec python -m uvicorn app.server:app --host 0.0.0.0 --port 8080
