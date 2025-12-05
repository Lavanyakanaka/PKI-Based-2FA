import base64
import binascii
import time
from typing import Tuple
import pyotp

def _hex_to_base32(hex_seed: str) -> str:
    # convert 64-char hex -> bytes -> base32 (no padding)
    if not isinstance(hex_seed, str) or len(hex_seed) != 64:
        raise ValueError("hex_seed must be a 64-character hex string")
    try:
        b = binascii.unhexlify(hex_seed)
    except (binascii.Error, TypeError) as e:
        raise ValueError(f"Invalid hex seed: {e}")
    b32 = base64.b32encode(b).decode('utf-8').strip('=')
    return b32

def generate_totp_code(hex_seed: str) -> str:
    """
    Generate current 6-digit TOTP code from a 64-char hex seed.
    Uses SHA-1, 30s period, 6 digits (pyotp defaults).
    """
    b32 = _hex_to_base32(hex_seed)
    totp = pyotp.TOTP(b32, digits=6, interval=30)
    return totp.now()

def verify_totp_code(hex_seed: str, code: str, valid_window: int = 1) -> bool:
    """
    Verify a 6-digit TOTP code with ±valid_window periods tolerance.
    """
    if not isinstance(code, str) or not code.isdigit() or len(code) not in (6,):
        raise ValueError("code must be a 6-digit numeric string")
    b32 = _hex_to_base32(hex_seed)
    totp = pyotp.TOTP(b32, digits=6, interval=30)
    return totp.verify(code, valid_window=valid_window)

def current_code_and_remaining(hex_seed: str) -> Tuple[str, int]:
    """
    Return (code, valid_for_seconds) where valid_for_seconds is seconds until period expiry.
    """
    now = int(time.time())
    period = 30
    elapsed = now % period
    remaining = period - elapsed
    code = generate_totp_code(hex_seed)
    return code, remaining

if __name__ == "__main__":
    # CLI: print current code and remaining seconds based on ./data/seed.txt
    import os, sys
    seed_path = os.path.join('.', 'data', 'seed.txt')
    if not os.path.isfile(seed_path):
        print("ERROR: seed not found at ./data/seed.txt", file=sys.stderr)
        sys.exit(2)
    seed = open(seed_path, 'r').read().strip()
    try:
        code, rem = current_code_and_remaining(seed)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(3)
    print(code)
    print(rem)
