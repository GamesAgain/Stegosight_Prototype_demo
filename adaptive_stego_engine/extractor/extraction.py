"""Low-level bit extraction logic."""
from __future__ import annotations

from typing import List

CHANNEL_ORDER = (2, 1, 0)


def extract_bits_low_level(stego_rgb: np.ndarray, order: np.ndarray, capacity_flat: np.ndarray) -> List[int]:
    flat = stego_rgb.reshape(-1, 3)
    bits: List[int] = []
    for pixel_index in order:
        cap = int(capacity_flat[pixel_index])
        if cap <= 0:
            continue
        for channel_offset in range(cap):
            channel = CHANNEL_ORDER[channel_offset % len(CHANNEL_ORDER)]
            bits.append(int(flat[pixel_index, channel] & 1))
    return bits
