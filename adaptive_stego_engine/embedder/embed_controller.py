"""High level embedding orchestration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
from tqdm import tqdm

from ..analyzer.texture_map import surface_map
from ..embedder import embedding
from ..embedder.capacity import capacity_to_bit_total, pixel_capacity
from ..embedder.drift_control import apply_mask, safe_capacity_mask
from ..embedder.noise_predictor import predictor_penalty
from ..embedder.pixel_order import ordered_pixels
from ..util import bitstream
from ..util.header import build_plain_header, encrypt_payload
from ..util.metrics import psnr, ssim


@dataclass
class EmbedResult:
    stego_image: np.ndarray
    psnr_value: float
    ssim_value: float
    bits_embedded: int
    capacity_bits: int


QUALITY_PSNR_THRESHOLD = 48.0
QUALITY_SSIM_THRESHOLD = 0.985


def _normalize_mode(mode: str | None) -> str:
    if not mode:
        return "AES-GCM"
    mode_upper = mode.upper()
    if "CTR" in mode_upper:
        return "AES-CTR"
    return "AES-GCM"


def prepare_payload(payload: bytes, password: str | None, mode: str | None, encrypt: bool) -> Tuple[bytes, int]:
    header = build_plain_header(len(payload))
    if not encrypt:
        data = bytes([0]) + header + payload
    else:
        normalized = _normalize_mode(mode)
        package = encrypt_payload(header, payload, password or "", normalized)
        encoded = package.encode()
        data = bytes([1]) + len(encoded).to_bytes(4, "big") + encoded
    return data, len(data)


class AdaptiveEmbedder:
    def __init__(self, seed: str, encrypt: bool, password: str | None = None, mode: str | None = None) -> None:
        self.seed = seed
        self.encrypt = encrypt
        self.password = password or ""
        self.mode = _normalize_mode(mode)

    def embed(self, image: np.ndarray, payload: bytes) -> EmbedResult:
        original = image.copy()
        surface, grad, entropy = surface_map(image)
        penalty = predictor_penalty(image)
        base_capacity = pixel_capacity(surface, penalty)
        mask = safe_capacity_mask(image, base_capacity)
        capacity = apply_mask(base_capacity, mask)
        total_capacity = capacity_to_bit_total(capacity)

        data_bytes, _ = prepare_payload(payload, self.password, self.mode, self.encrypt)
        bits = bitstream.bytes_to_bits(data_bytes)
        if len(bits) > total_capacity:
            raise ValueError("Payload too large for cover image capacity")

        order = ordered_pixels(entropy, self.seed)
        stego = image.copy()
        bit_index = 0
        for y, x in tqdm(order, desc="Embedding", leave=False):
            cap = int(capacity[y, x])
            if cap <= 0:
                continue
            if bit_index >= len(bits):
                break
            take = bits[bit_index: bit_index + cap]
            if len(take) < cap:
                break
            new_pixel = embedding.embed_bits_into_pixel(stego[y, x, :], take)
            stego[y, x, :] = new_pixel
            bit_index += cap
        if bit_index < len(bits):
            raise ValueError("Failed to embed all bits; capacity calculation mismatch")

        psnr_value = psnr(original, stego)
        ssim_value = ssim(original, stego)
        if psnr_value < QUALITY_PSNR_THRESHOLD or ssim_value < QUALITY_SSIM_THRESHOLD:
            raise ValueError("Quality thresholds not met after embedding")

        return EmbedResult(
            stego_image=stego,
            psnr_value=psnr_value,
            ssim_value=ssim_value,
            bits_embedded=len(bits),
            capacity_bits=total_capacity,
        )
