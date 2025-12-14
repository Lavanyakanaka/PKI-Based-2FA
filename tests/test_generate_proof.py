import base64
from pathlib import Path
import pytest

from app import generate_proof as gp


def test_instructor_key_size_mismatch_raises():
    # repository contains an instructor_public.pem that may be the wrong size
    instr_path = Path('instructor_public.pem')
    assert instr_path.exists()
    instr_pub = gp.load_public_key(instr_path)
    # current repo instructor key is 8192 bits and should cause our validation error
    if instr_pub.key_size != 4096:
        with pytest.raises(ValueError):
            # try encrypting arbitrary bytes which should trigger the key size check
            priv = gp.load_private_key(Path('student_private.pem'))
            sig = gp.sign_message('0'*40, priv)
            gp.encrypt_with_public_key(sig, instr_pub)


def test_encrypt_output_length_matches_keysize():
    # Use the student public key (4096 bits) as a stand-in for instructor 4096-bit key
    pub = gp.load_public_key(Path('student_public.pem'))
    priv = gp.load_private_key(Path('student_private.pem'))
    sig = gp.sign_message('a'*40, priv)
    # RSA-PSS signature length equals the signer's modulus size (512 bytes for 4096-bit keys)
    # which exceeds OAEP's max payload for a 4096-bit key; encryption should fail with a helpful error.
    with pytest.raises(ValueError, match="OAEP max payload"):
        gp.encrypt_with_public_key(sig, pub)
