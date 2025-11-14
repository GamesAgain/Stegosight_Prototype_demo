"""Cryptographic helpers for key derivation and symmetric encryption."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Tuple

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


ARGON_TIME_COST = 3
ARGON_MEMORY_COST = 102400  # in kibibytes (~100 MiB)
ARGON_PARALLELISM = 8
KEY_LENGTH = 32


@dataclass
class CipherResult:
    ciphertext: bytes
    nonce: bytes
    tag: bytes | None = None


def derive_key(password: str | bytes, salt: bytes, length: int = KEY_LENGTH) -> bytes:
    """Derive a symmetric key using Argon2id."""
    if isinstance(password, str):
        password_bytes = password.encode("utf-8")
    else:
        password_bytes = password
    return hash_secret_raw(
        password=password_bytes,
        salt=salt,
        time_cost=ARGON_TIME_COST,
        memory_cost=ARGON_MEMORY_COST,
        parallelism=ARGON_PARALLELISM,
        hash_len=length,
        type=Type.ID,
    )


def aes_gcm_encrypt(key: bytes, plaintext: bytes, associated_data: bytes = b"") -> CipherResult:
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(nonce, plaintext, associated_data)
    ciphertext, tag = ct[:-16], ct[-16:]
    return CipherResult(ciphertext=ciphertext, nonce=nonce, tag=tag)


def aes_gcm_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes, associated_data: bytes = b"") -> bytes:
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext + tag, associated_data)


def aes_ctr_hmac_encrypt(key: bytes, plaintext: bytes, associated_data: bytes = b"") -> CipherResult:
    nonce = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()

    h = hmac.HMAC(key, hashes.SHA256())
    h.update(associated_data)
    h.update(nonce)
    h.update(ciphertext)
    tag = h.finalize()
    return CipherResult(ciphertext=ciphertext, nonce=nonce, tag=tag)


def aes_ctr_hmac_decrypt(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes, associated_data: bytes = b"") -> bytes:
    h = hmac.HMAC(key, hashes.SHA256())
    h.update(associated_data)
    h.update(nonce)
    h.update(ciphertext)
    h.verify(tag)

    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
    decryptor = cipher.decryptor()
    return decryptor.update(ciphertext) + decryptor.finalize()


def random_salt(length: int = 16) -> bytes:
    return os.urandom(length)


def stretch_key(password: str | bytes, salt: bytes) -> Tuple[bytes, bytes]:
    """Derive both encryption and MAC keys from the same KDF output."""
    master = derive_key(password, salt, length=64)
    return master[:32], master[32:]
