"""Pixel ordering based on entropy + seeded shuffle."""
from __future__ import annotations

import numpy as np

from ..util import prng


def build_pixel_order(entropy_map: np.ndarray, seed: str) -> np.ndarray:
    flat_indices = np.arange(entropy_map.size, dtype=np.int64)
    sorted_indices = flat_indices[np.argsort(entropy_map.reshape(-1))[::-1]]
    shuffled = prng.shuffle_indices(sorted_indices, seed)
    return shuffled
