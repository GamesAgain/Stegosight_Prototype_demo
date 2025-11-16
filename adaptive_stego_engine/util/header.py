"""Header building/validation helpers."""
from __future__ import annotations

from typing import Tuple

from .crypto import aes_gcm_decrypt, aes_gcm_encrypt

MAGIC = b"STEGO"
HEADER_LEN = len(MAGIC) + 4


def build_plain_header(payload_len: int) -> bytes:
    if payload_len < 0:
        raise ValueError("Payload length cannot be negative")
    return MAGIC + payload_len.to_bytes(4, "big")


def validate_header(plain_header: bytes) -> int:
    if len(plain_header) != HEADER_LEN:
        raise ValueError("Header length mismatch")
    if not plain_header.startswith(MAGIC):
        raise ValueError("Magic mismatch")
    return int.from_bytes(plain_header[len(MAGIC):], "big")


def encrypt_header(plain_header: bytes, key: bytes) -> Tuple[bytes, bytes]:
    nonce, ciphertext = aes_gcm_encrypt(key, plain_header)
    return nonce, ciphertext


def decrypt_header(nonce: bytes, ciphertext: bytes, key: bytes) -> bytes:
    return aes_gcm_decrypt(key, nonce, ciphertext)
