#!/usr/bin/env python3
import sys, subprocess, base64
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding as asympadding
from cryptography.hazmat.backends import default_backend

def get_commit_hash():
    p = subprocess.run(["git", "log", "-1", "--format=%H"], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("Failed to get git commit hash: " + p.stderr.strip())
    h = p.stdout.strip()
    if len(h) != 40:
        raise RuntimeError("Unexpected commit hash: " + repr(h))
    return h

def load_private_key(path: Path):
    data = path.read_bytes()
    return serialization.load_pem_private_key(data, password=None, backend=default_backend())

def load_public_key(path: Path):
    data = path.read_bytes()
    return serialization.load_pem_public_key(data, backend=default_backend())

def sign_message(message: str, private_key):
    msg_bytes = message.encode("utf-8")
    sig = private_key.sign(
        msg_bytes,
        asympadding.PSS(
            mgf=asympadding.MGF1(hashes.SHA256()),
            salt_length=asympadding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return sig

def encrypt_with_public_key(data: bytes, public_key):
    ct = public_key.encrypt(
        data,
        asympadding.OAEP(
            mgf=asympadding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return ct

def main():
    try:
        commit_hash = get_commit_hash()
        priv_path = Path("student_private.pem")
        instr_path = Path("instructor_public.pem")
        if not priv_path.exists():
            raise FileNotFoundError("student_private.pem not found")
        if not instr_path.exists():
            raise FileNotFoundError("instructor_public.pem not found")
        priv = load_private_key(priv_path)
        instr_pub = load_public_key(instr_path)
        signature = sign_message(commit_hash, priv)
        encrypted = encrypt_with_public_key(signature, instr_pub)
        enc_b64 = base64.b64encode(encrypted).decode("ascii")
        # print as two lines for easy parsing
        print("Commit Hash:", commit_hash)
        print("Encrypted Signature (base64):", enc_b64)
        # also write to proof file
        with open("encrypted_signature.b64", "w") as f:
            f.write(enc_b64 + "\n")
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
