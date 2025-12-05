#!/usr/bin/env python3
"""Cron script to log 2FA codes every minute.

Reads /data/seed.txt (64-char hex), converts to base32 and emits:
YYYY-MM-DD HH:MM:SS - 2FA Code: XXXXXX

Errors are printed to stderr for cron to capture.
"""
import sys
import os
from datetime import datetime, timezone
import binascii

SEED_PATH = "/data/seed.txt"

def read_hex_seed():
    if not os.path.isfile(SEED_PATH):
        raise FileNotFoundError(f"seed file not found: {SEED_PATH}")
    s = open(SEED_PATH, "r").read().strip()
    if len(s) != 64:
        raise ValueError("seed must be a 64-character hex string")
    # validate hex
    try:
        binascii.unhexlify(s)
    except (binascii.Error, TypeError) as e:
        raise ValueError(f"invalid hex seed: {e}")
    return s

def hex_to_base32(hex_seed: str) -> str:
    b = binascii.unhexlify(hex_seed)
    import base64
    return base64.b32encode(b).decode('utf-8').strip('=')

def main():
    try:
        hex_seed = read_hex_seed()
        b32 = hex_to_base32(hex_seed)
        # lazy import so cron errors are explicit if dependency missing
        import pyotp
        totp = pyotp.TOTP(b32, digits=6, interval=30)
        code = totp.now()
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{ts} - 2FA Code: {code}")
    except Exception as e:
        # print error with traceback to stderr so cron log captures it
        import traceback
        print(f"ERROR: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        # non-zero exit code so cron may log failure (but we still let cron continue)
        sys.exit(1)

if __name__ == "__main__":
    main()
