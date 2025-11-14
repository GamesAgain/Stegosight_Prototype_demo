"""Core multi-bit LSB embedding logic."""
from __future__ import annotations

from typing import Iterable, List

import numpy as np
from tqdm import tqdm

from ..util.bitstream import bytes_to_bits
from . import noise_predictor, pixel_order
from .drift_control import DriftController


class EmbeddingError(Exception):
    pass


def _bits_to_int(bits: List[int]) -> int:
    value = 0
    for bit in bits:
        value = (value << 1) | (bit & 1)
    return value


def embed_payload(
    cover_image: np.ndarray,
    payload: bytes,
    capacity_map: np.ndarray,
    seed: str,
) -> tuple[np.ndarray, int]:
    stego = cover_image.copy()
    controller = DriftController(cover_image)
    bits = bytes_to_bits(payload)
    bit_index = 0
    indices = pixel_order.prioritized_pixel_indices(cover_image, seed)
    total_bits = len(bits)

    for y, x, channel in tqdm(indices, desc="Embedding", total=len(indices)):
        if bit_index >= total_bits:
            break
        desired = int(capacity_map[y, x])
        if desired <= 0:
            continue
        allowed = noise_predictor.adaptive_capacity(stego, y, x, channel, desired)
        if allowed <= 0:
            continue
        remaining = total_bits - bit_index
        use_bits = min(allowed, remaining)
        chunk = bits[bit_index : bit_index + use_bits]
        if not chunk:
            break

        old_value = int(stego[y, x, channel])
        mask = ~((1 << use_bits) - 1)
        new_value = (old_value & mask) | _bits_to_int(chunk)
        new_value = max(0, min(255, new_value))

        if new_value == old_value:
            bit_index += use_bits
            continue

        stego[y, x, channel] = new_value
        if not controller.validate_change(stego, y, x):
            stego[y, x, channel] = old_value
            continue
        bit_index += use_bits

    if bit_index < total_bits:
        raise EmbeddingError("Cover image capacity insufficient for payload")

    return stego, bit_index
