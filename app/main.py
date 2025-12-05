from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
import base64
import os
from app.crypto_utils import load_private_key, decrypt_seed
from app.totp_utils import generate_totp_code, verify_totp_code, read_hex_seed

app = FastAPI()

# Paths
SEED_PATH = Path("/data/seed.txt")
PRIVATE_KEY_PATH = Path("/srv/app/student_private.pem")

class SeedRequest(BaseModel):
    encrypted_seed: str

class VerifyRequest(BaseModel):
    code: str

@app.post("/decrypt-seed")
def api_decrypt_seed(req: SeedRequest):
    try:
        encrypted_seed = req.encrypted_seed
        if not encrypted_seed:
            raise ValueError("Missing encrypted seed")

        private_key = load_private_key(PRIVATE_KEY_PATH)
        hex_seed = decrypt_seed(encrypted_seed, private_key)

        # Store in persistent volume
        SEED_PATH.write_text(hex_seed)

        return {"status": "ok"}

    except Exception as e:
        return {"error": "Decryption failed"}

@app.get("/generate-2fa")
def api_generate_2fa():
    try:
        if not SEED_PATH.exists():
            raise FileNotFoundError("Seed not decrypted")

        hex_seed = read_hex_seed(SEED_PATH)
        code = generate_totp_code(hex_seed)

        # remaining seconds in current 30s window
        valid_for = 30 - (int(os.time.time()) % 30)

        return {"code": code, "valid_for": valid_for}

    except Exception:
        raise HTTPException(status_code=500, detail="Seed not decrypted yet")

@app.post("/verify-2fa")
def api_verify_2fa(req: VerifyRequest):
    try:
        if not req.code:
            raise HTTPException(status_code=400, detail="Missing code")

        if not SEED_PATH.exists():
            raise HTTPException(status_code=500, detail="Seed not decrypted yet")

        hex_seed = read_hex_seed(SEED_PATH)
        valid = verify_totp_code(hex_seed, req.code)

        return {"valid": valid}

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected error")
