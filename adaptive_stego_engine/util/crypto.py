"""Cryptographic primitives for the Adaptive Steganography Engine."""
from __future__ import annotations

import os
from dataclasses import dataclass

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


@dataclass
class EncryptionResult:
    nonce: bytes
    ciphertext: bytes
    tag: bytes


def generate_salt(length: int = 16) -> bytes:
    return os.urandom(length)


def derive_key(seed: str, salt: bytes, iterations: int = 200_000, length: int = 32) -> bytes:
    """Derive a symmetric key using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=iterations,
        backend=default_backend(),
    )
    return kdf.derive(seed.encode("utf-8"))


def aes_gcm_encrypt(key: bytes, plaintext: bytes, associated_data: bytes = b"") -> EncryptionResult:
    """Encrypt data with AES-GCM."""
    nonce = os.urandom(12)
    encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend()).encryptor()
    if associated_data:
        encryptor.authenticate_additional_data(associated_data)
    ciphertext = encryptor.update(plaintext) + encryptor.finalize()
    return EncryptionResult(nonce=nonce, ciphertext=ciphertext, tag=encryptor.tag)


def aes_gcm_decrypt(
    key: bytes,
    nonce: bytes,
    tag: bytes,
    ciphertext: bytes,
    associated_data: bytes = b"",
) -> bytes:
    """Decrypt AES-GCM data and return the plaintext."""
    decryptor = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend()).decryptor()
    if associated_data:
        decryptor.authenticate_additional_data(associated_data)
    plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return plaintext
