#!/usr/bin/env bash
set -e
# Start cron if not already running, then tail the cron output file so container keeps running if used
service cron start || cron || true
mkdir -p /cron
touch /cron/last_code.txt
tail -F /cron/last_code.txt
