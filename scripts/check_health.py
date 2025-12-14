#!/usr/bin/env python3
"""Simple healthcheck script used by Docker HEALTHCHECK.

Exits 0 when http://localhost:8080/health returns JSON {"status": "ok"} and 1 otherwise.
"""
import sys
import urllib.request
import json

URL = "http://localhost:8080/health"

MAX_ATTEMPTS = 5
BACKOFF = [1, 1, 2, 4, 8]

for attempt in range(MAX_ATTEMPTS):
	try:
		with urllib.request.urlopen(URL, timeout=5) as r:
			if r.status != 200:
				raise RuntimeError("status %s" % r.status)
			body = r.read()
			data = json.loads(body)
			if data.get("status") == "ok":
				sys.exit(0)
			raise RuntimeError("bad body")
	except Exception:
		# last attempt should exit non-zero, otherwise wait and retry
		if attempt == MAX_ATTEMPTS - 1:
			sys.exit(1)
		time_to_sleep = BACKOFF[attempt] if attempt < len(BACKOFF) else BACKOFF[-1]
		import time
		time.sleep(time_to_sleep)
