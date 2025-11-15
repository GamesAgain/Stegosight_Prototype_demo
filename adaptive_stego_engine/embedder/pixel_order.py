"""Pixel ordering for adaptive embedding."""
from __future__ import annotations

from typing import List, Tuple

import numpy as np

from ..util.prng import deterministic_shuffle


PixelIndex = Tuple[int, int]


def compute_pixel_order(entropy_map: np.ndarray, seed: str) -> List[PixelIndex]:
    """Sort pixels by entropy and shuffle deterministically with the seed."""
    coords = list(np.ndindex(entropy_map.shape))
    coords.sort(key=lambda idx: float(entropy_map[idx]), reverse=True)
    deterministic_shuffle(coords, seed)
    return coords
