"""Header construction and validation utilities."""
from __future__ import annotations

import struct
from dataclasses import dataclass

from .crypto import aes_gcm_decrypt, aes_gcm_encrypt, derive_key, generate_salt

MAGIC = b"STEGO"
HEADER_LEN = len(MAGIC) + 4


@dataclass
class EncryptedHeader:
    salt: bytes
    nonce: bytes
    tag: bytes
    ciphertext: bytes


def build_plain_header(payload_length: int) -> bytes:
    if payload_length < 0:
        raise ValueError("Payload length must be non-negative")
    return MAGIC + struct.pack(">I", payload_length)


def encrypt_header(seed: str, header: bytes, payload: bytes) -> EncryptedHeader:
    """Encrypt header + payload using AES-GCM."""
    salt = generate_salt()
    key = derive_key(seed, salt)
    result = aes_gcm_encrypt(key, header + payload)
    return EncryptedHeader(salt=salt, nonce=result.nonce, tag=result.tag, ciphertext=result.ciphertext)


def decrypt_header(seed: str, encrypted: EncryptedHeader) -> bytes:
    """Decrypt AES-GCM protected header and payload."""
    key = derive_key(seed, encrypted.salt)
    return aes_gcm_decrypt(key, encrypted.nonce, encrypted.tag, encrypted.ciphertext)


def validate_header(header: bytes) -> int:
    """Validate the header magic and return payload length."""
    if len(header) < HEADER_LEN:
        raise ValueError("Header too short")
    magic = header[: len(MAGIC)]
    if magic != MAGIC:
        raise ValueError("Invalid header magic; possible wrong password")
    length = struct.unpack(">I", header[len(MAGIC) : len(MAGIC) + 4])[0]
    return length
