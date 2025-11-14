"""Cryptographic primitives: Argon2id KDF, AES modes, and HMAC."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Tuple

from argon2.low_level import Type, hash_secret_raw
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


ARGON2_TIME_COST = 3
ARGON2_MEMORY_COST = 2 ** 16
ARGON2_PARALLELISM = 2
ARGON2_HASH_LEN = 32


@dataclass
class AESEncrypted:
    ciphertext: bytes
    nonce: bytes
    tag: bytes | None = None
    hmac_tag: bytes | None = None


def derive_key(password: str | bytes, salt: bytes, length: int = 32) -> bytes:
    if isinstance(password, str):
        password_bytes = password.encode("utf-8")
    else:
        password_bytes = password
    key = hash_secret_raw(
        secret=password_bytes,
        salt=salt,
        time_cost=ARGON2_TIME_COST,
        memory_cost=ARGON2_MEMORY_COST,
        parallelism=ARGON2_PARALLELISM,
        hash_len=length,
        type=Type.ID,
    )
    return key


def aes_gcm_encrypt(key: bytes, plaintext: bytes, associated_data: bytes | None = None) -> AESEncrypted:
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
    tag = ciphertext[-16:]
    data = ciphertext[:-16]
    return AESEncrypted(ciphertext=data, nonce=nonce, tag=tag)


def aes_gcm_decrypt(key: bytes, encrypted: AESEncrypted, associated_data: bytes | None = None) -> bytes:
    aesgcm = AESGCM(key)
    combined = encrypted.ciphertext + (encrypted.tag or b"")
    return aesgcm.decrypt(encrypted.nonce, combined, associated_data)


def aes_ctr_encrypt(key: bytes, plaintext: bytes) -> AESEncrypted:
    nonce = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CTR(nonce))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    tag = _hmac_sha256(key, nonce + ciphertext)
    return AESEncrypted(ciphertext=ciphertext, nonce=nonce, hmac_tag=tag)


def aes_ctr_decrypt(key: bytes, encrypted: AESEncrypted) -> bytes:
    expected_tag = _hmac_sha256(key, encrypted.nonce + encrypted.ciphertext)
    if expected_tag != encrypted.hmac_tag:
        raise ValueError("HMAC verification failed")
    cipher = Cipher(algorithms.AES(key), modes.CTR(encrypted.nonce))
    decryptor = cipher.decryptor()
    return decryptor.update(encrypted.ciphertext) + decryptor.finalize()


def _hmac_sha256(key: bytes, data: bytes) -> bytes:
    h = hmac.HMAC(key, hashes.SHA256())
    h.update(data)
    return h.finalize()
