"""Utilities to read embedded bits from stego image."""
from __future__ import annotations

from typing import Generator, Iterable, List, Tuple

import numpy as np

from ..embedder import noise_predictor, pixel_order


def _int_to_bits(value: int, width: int) -> List[int]:
    return [(value >> shift) & 1 for shift in range(width - 1, -1, -1)]


def read_bits(
    stego_image: np.ndarray,
    capacity_map: np.ndarray,
    seed: str,
) -> Generator[int, None, None]:
    indices = pixel_order.prioritized_pixel_indices(stego_image, seed)
    for y, x, channel in indices:
        desired = int(capacity_map[y, x])
        if desired <= 0:
            continue
        allowed = noise_predictor.adaptive_capacity(stego_image, y, x, channel, desired)
        if allowed <= 0:
            continue
        mask = (1 << allowed) - 1
        value = int(stego_image[y, x, channel]) & mask
        bits = _int_to_bits(value, allowed)
        for bit in bits:
            yield bit
