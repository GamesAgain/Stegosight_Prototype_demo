"""Bit/byte conversion helpers and stream packing."""
from __future__ import annotations

from typing import Dict, List

from .exceptions import StegoEngineError

MODE_SYMMETRIC = 0x01
MODE_ASYMMETRIC = 0x02


def bytes_to_bits(data: bytes) -> List[int]:
    bits: List[int] = []
    for byte in data:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits


def bits_to_bytes(bits: List[int]) -> bytes:
    if len(bits) % 8 != 0:
        bits = bits + [0] * (8 - (len(bits) % 8))
    out = bytearray()
    for i in range(0, len(bits), 8):
        value = 0
        for j in range(8):
            value = (value << 1) | (bits[i + j] & 1)
        out.append(value)
    return bytes(out)


def pack_symmetric_stream(
    *,
    salt: bytes,
    header_nonce: bytes,
    header_ct: bytes,
    payload_bytes: bytes,
    payload_encrypted: bool,
    payload_nonce: bytes | None,
) -> bytes:
    if len(salt) != 16:
        raise StegoEngineError("Salt must be 16 bytes")
    if len(header_nonce) != 12:
        raise StegoEngineError("Header nonce must be 12 bytes")
    if len(header_ct) != 25:
        raise StegoEngineError("Header ciphertext must be 25 bytes")
    stream = bytearray()
    stream.append(MODE_SYMMETRIC)
    stream += salt
    stream += header_nonce
    stream += header_ct
    stream.append(1 if payload_encrypted else 0)
    if payload_encrypted:
        if payload_nonce is None or len(payload_nonce) != 12:
            raise StegoEngineError("Payload nonce missing or invalid")
        stream += payload_nonce
    stream += payload_bytes
    return bytes(stream)


def unpack_symmetric_stream(data: bytes) -> Dict[str, bytes | bool]:
    if not data or data[0] != MODE_SYMMETRIC:
        raise StegoEngineError("Not a symmetric mode stream")
    idx = 1
    salt = data[idx : idx + 16]
    if len(salt) != 16:
        raise StegoEngineError("Corrupted salt in stream")
    idx += 16
    header_nonce = data[idx : idx + 12]
    idx += 12
    header_ct = data[idx : idx + 25]
    if len(header_ct) != 25:
        raise StegoEngineError("Corrupted header ciphertext")
    idx += 25
    if idx >= len(data):
        raise StegoEngineError("Stream truncated before payload flag")
    enc_flag = data[idx]
    idx += 1
    payload_encrypted = enc_flag == 1
    payload_nonce = b""
    if payload_encrypted:
        payload_nonce = data[idx : idx + 12]
        if len(payload_nonce) != 12:
            raise StegoEngineError("Corrupted payload nonce")
        idx += 12
    payload = data[idx:]
    return {
        "salt": salt,
        "header_nonce": header_nonce,
        "header_ct": header_ct,
        "payload_encrypted": payload_encrypted,
        "payload_nonce": payload_nonce,
        "payload_data": payload,
    }


def pack_public_stream(*, ek: bytes, aes_nonce: bytes, aes_ct: bytes) -> bytes:
    if len(aes_nonce) != 12:
        raise StegoEngineError("AES nonce must be 12 bytes")
    if len(ek) >= 2 ** 16:
        raise StegoEngineError("Encrypted key too long")
    stream = bytearray()
    stream.append(MODE_ASYMMETRIC)
    stream += len(ek).to_bytes(2, "big")
    stream += ek
    stream += aes_nonce
    stream += aes_ct
    return bytes(stream)


def unpack_public_stream(data: bytes) -> Dict[str, bytes]:
    if not data or data[0] != MODE_ASYMMETRIC:
        raise StegoEngineError("Not a public-key stream")
    idx = 1
    key_len = int.from_bytes(data[idx : idx + 2], "big")
    idx += 2
    ek = data[idx : idx + key_len]
    if len(ek) != key_len:
        raise StegoEngineError("Corrupted RSA section")
    idx += key_len
    aes_nonce = data[idx : idx + 12]
    if len(aes_nonce) != 12:
        raise StegoEngineError("Corrupted AES nonce")
    idx += 12
    aes_ct = data[idx:]
    if not aes_ct:
        raise StegoEngineError("Missing AES ciphertext")
    return {"ek": ek, "aes_nonce": aes_nonce, "aes_ct": aes_ct}
