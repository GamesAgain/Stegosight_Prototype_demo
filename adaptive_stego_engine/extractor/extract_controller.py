"""High-level extraction orchestration."""
from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..util import crypto, header as header_util
from ..util.header import MODE_CTR_HMAC, MODE_GCM
from .extraction import BitStreamReader, ExtractionError, acquire_bit_reader


@dataclass
class ExtractResult:
    header: bytes
    payload: bytes
    encrypted: bool
    mode: Optional[str]


class HeaderValidationError(Exception):
    pass


def _parse_plain_package(reader: BitStreamReader) -> tuple[bytes, bytes]:
    header = reader.read_bytes(9)
    length = header_util.validate_header(header)
    payload = reader.read_bytes(length)
    return header, payload


def _read_length(reader: BitStreamReader, fmt: str) -> int:
    size = struct.calcsize(fmt)
    data = reader.read_bytes(size)
    return struct.unpack(fmt, data)[0]


def _parse_encrypted_package(reader: BitStreamReader) -> dict:
    mode_byte = reader.read_bytes(1)[0]
    salt_length = reader.read_bytes(1)[0]
    salt = reader.read_bytes(salt_length)
    header_nonce_length = reader.read_bytes(1)[0]
    header_nonce = reader.read_bytes(header_nonce_length)
    header_tag_length = reader.read_bytes(1)[0]
    header_tag = reader.read_bytes(header_tag_length)
    header_cipher_length = _read_length(reader, ">H")
    header_cipher = reader.read_bytes(header_cipher_length)
    payload_nonce_length = reader.read_bytes(1)[0]
    payload_nonce = reader.read_bytes(payload_nonce_length)
    payload_tag_length = reader.read_bytes(1)[0]
    payload_tag = reader.read_bytes(payload_tag_length)
    payload_cipher_length = _read_length(reader, ">I")
    payload_cipher = reader.read_bytes(payload_cipher_length)

    if mode_byte not in (1, 2):
        raise ExtractionError("Unsupported encryption mode in package")
    mode = header_util.MODE_GCM if mode_byte == 1 else header_util.MODE_CTR_HMAC
    enc_header = header_util.EncryptedHeader(
        salt=salt,
        nonce=header_nonce,
        tag=header_tag,
        ciphertext=header_cipher,
        mode=mode,
    )
    payload_package = {
        "mode": mode,
        "nonce": payload_nonce,
        "tag": payload_tag,
        "ciphertext": payload_cipher,
    }
    return {"mode": mode, "header": enc_header, "payload": payload_package}


def extract(
    stego_image: np.ndarray,
    seed: str,
    password: Optional[str] = None,
) -> ExtractResult:
    reader = acquire_bit_reader(stego_image, seed)
    flag = reader.read_bytes(1)[0]

    if flag == 0:
        header, payload = _parse_plain_package(reader)
        return ExtractResult(header=header, payload=payload, encrypted=False, mode=None)

    if password is None:
        raise ExtractionError("Encrypted payload requires password")

    package_meta = _parse_encrypted_package(reader)
    enc_header = package_meta["header"]
    mode = package_meta["mode"]

    try:
        header_plain = header_util.decrypt_header(enc_header, password)
    except Exception as exc:  # pragma: no cover - cryptographic failure
        raise HeaderValidationError("Failed to decrypt header") from exc

    try:
        payload_length = header_util.validate_header(header_plain)
    except ValueError as exc:
        raise HeaderValidationError("Invalid header signature") from exc

    key = crypto.derive_key(password, enc_header.salt)
    payload_meta = package_meta["payload"]
    try:
        if mode == MODE_GCM:
            payload_bytes = crypto.aes_gcm_decrypt(
                key,
                payload_meta["nonce"],
                payload_meta["ciphertext"],
                payload_meta["tag"],
            )
        else:
            payload_bytes = crypto.aes_ctr_hmac_decrypt(
                key,
                payload_meta["nonce"],
                payload_meta["ciphertext"],
                payload_meta["tag"],
            )
    except Exception as exc:  # pragma: no cover - cryptographic failure
        raise ExtractionError("Failed to decrypt payload") from exc

    if len(payload_bytes) != payload_length:
        payload_bytes = payload_bytes[:payload_length]
    return ExtractResult(header=header_plain, payload=payload_bytes, encrypted=True, mode=mode)
