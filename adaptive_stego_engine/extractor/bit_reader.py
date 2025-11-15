"""Read embedded bitstreams from stego images."""
from __future__ import annotations

from typing import List, Sequence, Tuple

import numpy as np


PixelIndex = Tuple[int, int]


def extract_bits(
    image: np.ndarray,
    pixel_indices: Sequence[PixelIndex],
    capacities: np.ndarray,
    max_bits: int | None = None,
) -> List[int]:
    """Extract bits following the provided pixel order."""
    bits: List[int] = []
    for y, x in pixel_indices:
        cap = int(capacities[y, x])
        if cap <= 0:
            continue
        pixel = image[y, x]
        for channel in range(cap):
            bits.append(int(pixel[channel] & 1))
            if max_bits is not None and len(bits) >= max_bits:
                return bits
    return bits
