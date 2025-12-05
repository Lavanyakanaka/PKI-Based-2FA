import os
import sys
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import logging

# local utilities
from app.crypto_utils import decrypt_seed
from app.totp_utils import generate_totp_code, verify_totp_code, current_code_and_remaining

LOG = logging.getLogger("uvicorn.error")

DATA_DIR = Path(os.environ.get("DATA_DIR", "./data"))
SEED_PATH = DATA_DIR / "seed.txt"
PRIVATE_KEY_PATH = Path("student_private.pem")

app = FastAPI(title="PKI-TOTP Auth Microservice")


class DecryptRequest(BaseModel):
    encrypted_seed: str


class VerifyRequest(BaseModel):
    code: str


@app.post("/decrypt-seed")
async def post_decrypt_seed(req: DecryptRequest):
    # Validate inputs
    if not req.encrypted_seed:
        raise HTTPException(status_code=400, detail={"error": "Missing encrypted_seed"})
    # Ensure private key exists
    if not PRIVATE_KEY_PATH.is_file():
        LOG.error("Private key not found at %s", PRIVATE_KEY_PATH)
        raise HTTPException(status_code=500, detail={"error": "Private key missing"})
    # Attempt decryption
    try:
        seed = decrypt_seed(req.encrypted_seed, str(PRIVATE_KEY_PATH))
    except Exception as e:
        LOG.exception("Decryption failed")
        raise HTTPException(status_code=500, detail={"error": "Decryption failed"})
    # Ensure data directory exists and write seed (single-line, no literal \n)
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(SEED_PATH, "w", newline="\n") as f:
            f.write(seed + "\n")
    except Exception as e:
        LOG.exception("Failed to write seed file")
        raise HTTPException(status_code=500, detail={"error": "Failed to persist seed"})
    return {"status": "ok"}


@app.get("/generate-2fa")
async def get_generate_2fa():
    # Check seed exists
    if not SEED_PATH.is_file():
        LOG.error("Seed file not found at %s", SEED_PATH)
        raise HTTPException(status_code=500, detail={"error": "Seed not decrypted yet"})
    try:
        seed = SEED_PATH.read_text().strip()
        code, remaining = current_code_and_remaining(seed)
        return {"code": code, "valid_for": remaining}
    except Exception as e:
        LOG.exception("Failed to generate 2FA")
        raise HTTPException(status_code=500, detail={"error": "Failed to generate 2FA"})


@app.post("/verify-2fa")
async def post_verify_2fa(req: VerifyRequest):
    # Validate input
    if not req.code:
        raise HTTPException(status_code=400, detail={"error": "Missing code"})
    if not SEED_PATH.is_file():
        LOG.error("Seed file not found at %s", SEED_PATH)
        raise HTTPException(status_code=500, detail={"error": "Seed not decrypted yet"})
    try:
        seed = SEED_PATH.read_text().strip()
        valid = verify_totp_code(seed, req.code, valid_window=1)
        return {"valid": bool(valid)}
    except ValueError as ve:
        LOG.exception("Bad request")
        raise HTTPException(status_code=400, detail={"error": str(ve)})
    except Exception as e:
        LOG.exception("Verification error")
        raise HTTPException(status_code=500, detail={"error": "Verification failed"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.server:app", host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), log_level="info")
