#!/usr/bin/env python3
"""
Cron job: read seed from /data/seed.txt, generate current TOTP code, and print a UTC timestamped line:
YYYY-MM-DD HH:MM:SS - 2FA Code: XXXXXX

Writes to stdout (cron will redirect to /cron/last_code.txt). Errors go to stderr.
"""
import sys
import os
from datetime import datetime
import traceback

try:
    import pyotp
    import binascii
except Exception as e:
    print("ERROR: missing dependency in cron job: {}".format(e), file=sys.stderr)
    sys.exit(1)

SEED_PATH = "/data/seed.txt"

def read_seed():
    if not os.path.isfile(SEED_PATH):
        raise FileNotFoundError("seed file not found at {}".format(SEED_PATH))
    s = open(SEED_PATH, "r").read().strip()
    if len(s) != 64:
        raise ValueError("seed must be 64-char hex")
    try:
        b = binascii.unhexlify(s)
    except Exception as e:
        raise ValueError("invalid hex seed: {}".format(e))
    # base32 (no padding) as used by TOTP libs
    import base64
    b32 = base64.b32encode(b).decode('utf-8').strip('=')
    return b32

def main():
    try:
        b32 = read_seed()
        totp = pyotp.TOTP(b32, digits=6, interval=30)
        code = totp.now()
        ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{ts} - 2FA Code: {code}")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(2)

if __name__ == "__main__":
    main()
