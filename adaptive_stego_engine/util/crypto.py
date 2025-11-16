"""Symmetric cryptographic primitives."""
from __future__ import annotations

import os
from typing import Optional, Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


PBKDF2_ITERATIONS = 100_000
PBKDF2_SALT_LEN = 16
AES_NONCE_LEN = 12
AES_TAG_LEN = 16


def derive_key_pbkdf2(
    password: str,
    salt: bytes,
    length: int = 32,
    iterations: int = PBKDF2_ITERATIONS,
) -> bytes:
    if not password:
        raise ValueError("Password must not be empty")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(password.encode("utf-8"))


def aes_gcm_encrypt(key: bytes, plaintext: bytes, aad: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    nonce = os.urandom(AES_NONCE_LEN)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, aad)
    return nonce, ciphertext


def aes_gcm_decrypt(
    key: bytes,
    nonce: bytes,
    ct_with_tag: bytes,
    aad: Optional[bytes] = None,
) -> bytes:
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ct_with_tag, aad)
