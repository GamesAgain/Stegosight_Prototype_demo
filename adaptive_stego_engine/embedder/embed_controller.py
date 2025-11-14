"""High-level orchestration for adaptive embedding."""
from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..util import crypto, header as header_util, metrics
from ..util.header import MODE_CTR_HMAC, MODE_GCM
from . import capacity as capacity_module
from .embedding import EmbeddingError, embed_payload


@dataclass
class EmbedResult:
    stego_image: np.ndarray
    psnr: float
    ssim: float
    package: bytes


MODE_MAP = {
    MODE_GCM: 1,
    MODE_CTR_HMAC: 2,
}

MODE_REVERSE_MAP = {v: k for k, v in MODE_MAP.items()}


class QualityError(Exception):
    pass


class EncryptionError(Exception):
    pass


def _serialize_encrypted_package(
    enc_header: header_util.EncryptedHeader,
    payload_result: crypto.CipherResult,
) -> bytes:
    mode_byte = MODE_MAP[enc_header.mode]
    salt = enc_header.salt
    header_cipher = enc_header.ciphertext
    header_nonce = enc_header.nonce
    header_tag = enc_header.tag
    payload_cipher = payload_result.ciphertext
    payload_nonce = payload_result.nonce
    payload_tag = payload_result.tag or b""

    parts = [
        b"\x01",
        struct.pack("B", mode_byte),
        struct.pack("B", len(salt)),
        salt,
        struct.pack("B", len(header_nonce)),
        header_nonce,
        struct.pack("B", len(header_tag)),
        header_tag,
        struct.pack(">H", len(header_cipher)),
        header_cipher,
        struct.pack("B", len(payload_nonce)),
        payload_nonce,
        struct.pack("B", len(payload_tag)),
        payload_tag,
        struct.pack(">I", len(payload_cipher)),
        payload_cipher,
    ]
    return b"".join(parts)


def _serialize_plain_package(header: bytes, payload: bytes) -> bytes:
    return b"\x00" + header + payload


def embed(
    cover_image: np.ndarray,
    payload: bytes,
    seed: str,
    password: Optional[str] = None,
    mode: str = MODE_GCM,
) -> EmbedResult:
    if password and not password.strip():
        raise EncryptionError("Password must not be empty when encryption is enabled")

    capacity_map, _ = capacity_module.compute_capacity(cover_image)
    header_plain = header_util.build_plain_header(len(payload))

    if password is None:
        package = _serialize_plain_package(header_plain, payload)
    else:
        if mode not in MODE_MAP:
            raise EncryptionError(f"Unsupported mode: {mode}")
        salt = crypto.random_salt()
        enc_header = header_util.encrypt_header(header_plain, password, mode, salt=salt)
        key = crypto.derive_key(password, salt)
        if mode == MODE_GCM:
            payload_result = crypto.aes_gcm_encrypt(key, payload)
        else:
            payload_result = crypto.aes_ctr_hmac_encrypt(key, payload)
        package = _serialize_encrypted_package(enc_header, payload_result)

    stego, _ = embed_payload(cover_image, package, capacity_map, seed)

    psnr_value = metrics.psnr(cover_image, stego)
    ssim_value = metrics.ssim(cover_image, stego)
    if psnr_value < 48.0 or ssim_value < 0.985:
        raise QualityError("Embedding quality thresholds not met")

    return EmbedResult(stego_image=stego, psnr=psnr_value, ssim=ssim_value, package=package)
