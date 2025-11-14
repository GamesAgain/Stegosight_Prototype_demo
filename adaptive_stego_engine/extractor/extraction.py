"""Low-level bit extraction mirroring the embedder."""
from __future__ import annotations

from typing import List

import numpy as np

from ..analyzer.texture_map import surface_map
from ..embedder.capacity import pixel_capacity
from ..embedder.drift_control import apply_mask, safe_capacity_mask
from ..embedder.noise_predictor import predictor_penalty
from ..embedder.pixel_order import ordered_pixels
from ..embedder.embedding import extract_bits_from_pixel


def extract_bits(image: np.ndarray, seed: str) -> List[int]:
    surface, grad, entropy = surface_map(image)
    penalty = predictor_penalty(image)
    base_capacity = pixel_capacity(surface, penalty)
    mask = safe_capacity_mask(image, base_capacity)
    capacity = apply_mask(base_capacity, mask)
    order = ordered_pixels(entropy, seed)

    bits: List[int] = []
    for y, x in order:
        cap = int(capacity[y, x])
        if cap <= 0:
            continue
        bits.extend(extract_bits_from_pixel(image[y, x, :], cap))
    return bits
