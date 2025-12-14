#!/usr/bin/env bash
set -euo pipefail

# Start cron (background). If service command is unavailable, fall back to cron.
service cron start || cron || true

# Ensure cron log file exists
mkdir -p /cron
touch /cron/last_code.txt

echo "entrypoint: started at $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> /cron/last_code.txt

# Run uvicorn in a monitored loop so the container remains up even if the app crashes.
while true; do
  echo "entrypoint: launching uvicorn at $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a /cron/last_code.txt
  # run uvicorn unbuffered; log stdout/stderr to both cron log and container stdout/stderr
  # so `docker logs` and mounted /cron/last_code.txt both contain the app logs
  python -u -m uvicorn app.server:app --host 0.0.0.0 --port 8080 2>&1 | tee -a /cron/last_code.txt || true
  echo "entrypoint: uvicorn exited at $(date -u +%Y-%m-%dT%H:%M:%SZ), sleeping before restart" >> /cron/last_code.txt
  sleep 5
done
