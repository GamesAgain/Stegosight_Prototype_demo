"""Multi-bit LSB embedding primitives."""
from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

import numpy as np

PixelModifications = List[Tuple[int, int, np.ndarray]]


def embed_bits(
    image: np.ndarray,
    pixel_indices: Sequence[tuple[int, int]],
    capacities: np.ndarray,
    bits: Sequence[int],
    start_index: int = 0,
) -> tuple[int, PixelModifications]:
    """Embed bits into the image following the provided pixel order."""
    modifications: PixelModifications = []
    idx = start_index
    total_bits = len(bits)

    for y, x in pixel_indices:
        if idx >= total_bits:
            break

        cap = int(capacities[y, x])
        if cap <= 0:
            continue

        bit_slice = bits[idx : min(idx + cap, total_bits)]
        if not bit_slice:
            break

        original_pixel = image[y, x].copy()
        modified_pixel = original_pixel.copy()

        for channel, bit in enumerate(bit_slice):
            channel_idx = channel % 3
            modified_pixel[channel_idx] = (modified_pixel[channel_idx] & ~1) | int(bit)

        image[y, x] = modified_pixel
        modifications.append((y, x, original_pixel))
        idx += len(bit_slice)

    return idx, modifications


def rollback(image: np.ndarray, modifications: PixelModifications) -> None:
    """Undo pixel modifications after a failed drift control check."""
    for y, x, original_pixel in modifications:
        image[y, x] = original_pixel
