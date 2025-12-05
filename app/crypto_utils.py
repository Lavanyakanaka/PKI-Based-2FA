import os
import re
import base64
from typing import Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend

HEX64_RE = re.compile(r'^[0-9a-f]{64}$')

def decrypt_seed(encrypted_seed_b64: str, private_key_pem_path: str, password: Optional[bytes]=None) -> str:
    """
    Decrypt base64-encoded encrypted seed using RSA/OAEP (SHA-256 / MGF1).
    Args:
        encrypted_seed_b64: Base64-encoded ciphertext
        private_key_pem_path: Path to PEM private key file
        password: Optional password bytes for encrypted PEM (if any)
    Returns:
        Decrypted hex seed (64-character lowercase hex string)
    Raises:
        ValueError on invalid input or decryption failure.
    """
    # load private key
    if not os.path.isfile(private_key_pem_path):
        raise ValueError(f"private key file not found: {private_key_pem_path}")

    with open(private_key_pem_path, "rb") as f:
        key_data = f.read()
    try:
        private_key = serialization.load_pem_private_key(key_data, password=password, backend=default_backend())
    except Exception as e:
        raise ValueError(f"Failed to load private key: {e}")

    # decode base64
    try:
        ct = base64.b64decode(encrypted_seed_b64)
    except Exception as e:
        raise ValueError(f"Base64 decode failed: {e}")

    # decrypt with OAEP(SHA-256, MGF1(SHA-256))
    try:
        pt = private_key.decrypt(
            ct,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")

    # decode to string and normalize
    try:
        seed = pt.decode("utf-8").strip()
    except Exception as e:
        raise ValueError(f"Failed to decode plaintext to UTF-8: {e}")

    seed = seed.lower()
    # validate 64-character hex
    if not isinstance(seed, str) or len(seed) != 64 or not HEX64_RE.match(seed):
        raise ValueError(f"Decrypted seed validation failed. Expect 64-char hex, got: {repr(seed)}")

    return seed

if __name__ == "__main__":
    # CLI helper: decrypt encrypted_seed.txt and write to ./data/seed.txt (create data folder)
    import sys
    enc_file = "encrypted_seed.txt"
    priv_key = "student_private.pem"
    out_dir = os.path.join(".", "data")
    out_path = os.path.join(out_dir, "seed.txt")

    if not os.path.isfile(enc_file):
        print(f"ERROR: {enc_file} not found in current directory.", file=sys.stderr)
        sys.exit(2)
    with open(enc_file, "r") as f:
        enc = f.read().strip()

    try:
        seed = decrypt_seed(enc, priv_key)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(3)

    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(seed + "\\n")
    print(f"Decrypted seed written to {out_path}")
