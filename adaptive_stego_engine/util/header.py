"""Header construction and validation helpers."""
from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Literal

from . import crypto

HEADER_MAGIC = b"STEGO"
MODE_GCM: Literal["AES-GCM"] = "AES-GCM"
MODE_CTR_HMAC: Literal["AES-CTR-HMAC"] = "AES-CTR-HMAC"


@dataclass
class EncryptedHeader:
    salt: bytes
    nonce: bytes
    tag: bytes
    ciphertext: bytes
    mode: str


@dataclass
class EncryptionPackage:
    header: EncryptedHeader
    payload: crypto.CipherResult


def build_plain_header(payload_length: int) -> bytes:
    if payload_length < 0:
        raise ValueError("payload_length must be non-negative")
    return HEADER_MAGIC + struct.pack(">I", payload_length)


def encrypt_header(header: bytes, password: str, mode: str, salt: bytes | None = None) -> EncryptedHeader:
    salt = salt or crypto.random_salt()
    key = crypto.derive_key(password, salt)
    if mode == MODE_GCM:
        res = crypto.aes_gcm_encrypt(key, header)
    elif mode == MODE_CTR_HMAC:
        res = crypto.aes_ctr_hmac_encrypt(key, header)
    else:
        raise ValueError(f"Unsupported encryption mode: {mode}")
    return EncryptedHeader(salt=salt, nonce=res.nonce, tag=res.tag or b"", ciphertext=res.ciphertext, mode=mode)


def decrypt_header(enc: EncryptedHeader, password: str) -> bytes:
    key = crypto.derive_key(password, enc.salt)
    if enc.mode == MODE_GCM:
        return crypto.aes_gcm_decrypt(key, enc.nonce, enc.ciphertext, enc.tag or b"")
    elif enc.mode == MODE_CTR_HMAC:
        return crypto.aes_ctr_hmac_decrypt(key, enc.nonce, enc.ciphertext, enc.tag or b"")
    else:
        raise ValueError(f"Unsupported encryption mode: {enc.mode}")


def validate_header(header: bytes) -> int:
    if len(header) < 9:
        raise ValueError("Header too short")
    magic = header[: len(HEADER_MAGIC)]
    if magic != HEADER_MAGIC:
        raise ValueError("Header magic mismatch")
    (length,) = struct.unpack(">I", header[len(HEADER_MAGIC) : len(HEADER_MAGIC) + 4])
    return length
