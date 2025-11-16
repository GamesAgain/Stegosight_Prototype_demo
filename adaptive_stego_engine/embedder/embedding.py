"""Low-level embedding primitives."""
from __future__ import annotations

from typing import Dict, List

import numpy as np

from ..util.exceptions import StegoEngineError

CHANNEL_ORDER = (2, 1, 0)  # B, G, R


def embed_bits_low_level(
    rgb: np.ndarray,
    order: np.ndarray,
    capacity_flat: np.ndarray,
    bits: List[int],
    block_map: np.ndarray,
    block_done: np.ndarray,
    block_pixel_positions: Dict[int, List[int]],
    gray_for_coords: np.ndarray,
    adjust_capacity_fn,
    block_safety_checker,
) -> np.ndarray:
    stego = rgb.copy()
    flat = stego.reshape(-1, 3)
    orig_flat = rgb.reshape(-1, 3)
    height, width = gray_for_coords.shape
    bit_idx = 0
    total_bits = len(bits)
    block_visit_counts = np.zeros_like(block_done, dtype=np.int32)
    block_finalized = np.zeros_like(block_done, dtype=bool)

    for pixel_index in order:
        if bit_idx >= total_bits:
            break
        block_id = int(block_map[pixel_index])
        if block_done[block_id]:
            continue
        cap = int(capacity_flat[pixel_index])
        if cap <= 0:
            block_visit_counts[block_id] += 1
            continue
        y = pixel_index // width
        x = pixel_index % width
        cap = adjust_capacity_fn(gray_for_coords, y, x, cap)
        if cap <= 0:
            block_visit_counts[block_id] += 1
            continue
        for channel_offset in range(cap):
            if bit_idx >= total_bits:
                break
            channel = CHANNEL_ORDER[channel_offset % len(CHANNEL_ORDER)]
            flat[pixel_index, channel] = (flat[pixel_index, channel] & ~1) | bits[bit_idx]
            bit_idx += 1
        block_visit_counts[block_id] += 1
        positions = block_pixel_positions[block_id]
        if not block_finalized[block_id] and block_visit_counts[block_id] >= len(positions):
            original_block = orig_flat[positions]
            stego_block = flat[positions]
            safe = block_safety_checker(original_block, stego_block)
            if not safe:
                flat[positions] = orig_flat[positions]
                block_done[block_id] = True
            block_finalized[block_id] = True

    if bit_idx < total_bits:
        raise StegoEngineError(
            f"Insufficient safe capacity: embedded {bit_idx} / {total_bits} bits"
        )

    return flat.reshape(rgb.shape)
