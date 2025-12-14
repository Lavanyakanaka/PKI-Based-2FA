## PKI-Based 2FA Microservice (Dockerized)

This project implements a PKI-based Two-Factor Authentication (2FA) microservice using RSA 4096-bit key pairs, encrypted TOTP seed exchange, secure decryption, persistent storage, and cron-based TOTP generation inside Docker.

- The microservice provides:

- RSA seed decryption

- TOTP code generation

- TOTP code verification

- Containerized runtime with cron automation

Persistent volumes for encrypted seed + cron logs

This project fully satisfies the required GPP task specification.

## 1. Features
Secure PKI workflow

Student RSA private key decrypts encrypted seed from the instructor.

Decrypted hex seed stored persistently in /data/seed.txt.

TOTP generation & verification

6-digit codes

30-second validity

SHA-1 algorithm

Cron-driven TOTP

Docker cron generates codes every minute

Logs stored in /cron/last_code.txt

FastAPI Endpoints\
POST /decrypt-seed\
GET  /generate-2fa\
POST /verify-2fa

## 2. Project Structure


PKI-Based-2FA-Microservice/
│
├── app/
│   ├── crypto_utils.py
│   ├── generate_proof.py
│   ├── server.py
│   └── totp_utils.py
│
├── scripts/
│   ├── run_uvicorn.sh
│   ├── run_cron.sh
│   ├── cron_job.py
│   └── log_2fa_cron.py
│
├── cron/
│   └── totp_cron
│
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
├── encrypted_signature.b64
├── encrypted_seed.b64
├── student_private.pem
├── student_public.pem
├── instructor_public.pem
└── README.md


## 3. Build Docker Image

Run this inside your project root:

docker build -t pki-2fa .

## 4. Run the Microservice (with persistent volumes)
Git Bash (Windows)\
docker run --rm --name pki-2fa-run -p 8080:8080 \
  -v "$(pwd)/docker_data:/data" \
  -v "$(pwd)/docker_cron:/cron" \
  pki-2fa

PowerShell\
docker run --rm --name pki-2fa-run -p 8080:8080 `
  -v "$PWD/docker_data:/data" `
  -v "$PWD/docker_cron:/cron" `
  pki-2fa


Ensure these host folders exist:

mkdir -p docker_data docker_cron

## 5. Decrypt the Encrypted Seed

You received an encrypted seed file from the instructor API.

Run:

curl -X POST "http://localhost:8080/decrypt-seed" \
  -H "Content-Type: application/json" \
  -d "{\"encrypted_seed\": \"$(cat encrypted_seed.txt)\"}"


If successful:

{"status": "ok"}


Check seed was persisted:

cat docker_data/seed.txt

## 6. Generate TOTP Code
curl http://localhost:8080/generate-2fa


Example output:

{
  "code": "482991",
  "valid_for": 17
}

## 7. Verify TOTP Code

curl -X POST "http://localhost:8080/verify-2fa" \
  -H "Content-Type: application/json" \
  -d "{\"code\": \"482991\"}"


Example response:

{"valid": true}
## 8. Cron-Generated TOTP (Automatic)

Cron inside Docker runs *every minute* and executes:

bash
* * * * * root python /srv/app/scripts/cron_job.py >> /cron/last_code.txt 2>&1
To check the generated TOTP codes (stored on your host machine):


cat docker_cron/last_code.txt
Example Output
2025-12-04 10:27:01 - 2FA Code: 995965
2025-12-04 10:28:01 - 2FA Code: 327754
2025-12-04 10:29:01 - 2FA Code: 827470

---

## 9. Environment Notes

Container timezone is set to UTC

Cron installed and started inside container

/data and /cron are persistent through Docker volumes

## 10. Requirements

Python packages (installed by Docker):

fastapi
uvicorn[standard]
cryptography
pyotp

## 11. Running with Docker Compose (Optional)
docker compose up --build

## 12. Submission Checklist (All Must Be True)
bash

 Dockerfile included
 RSA keys included
 encrypted_seed.b64 included
 FastAPI microservice running
 /decrypt-seed produces docker_data/seed.txt
 /generate-2fa works
 /verify-2fa works
 Cron updates docker_cron/last_code.txt
 Project builds & runs cleanly in Docker

## Commit Proof Notes

The commit-proof workflow signs the latest commit with the student's RSA private key and encrypts the signature with the instructor's RSA public key using OAEP. Be aware:

- RSA-PSS signatures are the same length as the signer's RSA modulus (e.g., 512 bytes for a 4096-bit key) and may exceed OAEP's maximum payload for a recipient RSA key of the same size.
- If `instructor_public.pem` is a different size than the grader's private key (for example, 8192-bit in the repository but the grader uses 4096-bit), decryption will fail with "Ciphertext length must be equal to key size.".
- To avoid this problem, ensure you use the instructor's provided 4096-bit public key, or switch to a hybrid encryption scheme (encrypt the signature with a symmetric key and encrypt that key with RSA) or a compact signature algorithm.

The `generate_proof.py` script now validates the instructor public key size and gives helpful errors if encryption will not succeed.

## Container Robustness

The container now uses a resilient `scripts/entrypoint.sh` that starts `cron` and runs `uvicorn` inside a monitored loop. If the application process exits unexpectedly, the entrypoint logs the failure to `/cron/last_code.txt` and restarts `uvicorn` after a short delay. This helps avoid rapid crash/restart loops and makes logs available to graders when diagnosing failures.


## 13. Author

Kella Kanaka Lavanya\
PKI-Based 2FA Microservice — GPP Mandatory Task
Built with FastAPI + Cryptography + Docker + Cron