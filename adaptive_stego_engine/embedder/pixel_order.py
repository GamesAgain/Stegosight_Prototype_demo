"""Pixel ordering logic: entropy sorting followed by PRNG shuffle."""
from __future__ import annotations

from typing import List, Tuple

import numpy as np

from ..util.prng import DeterministicPRNG


def ordered_pixels(entropy_map: np.ndarray, seed: str) -> List[Tuple[int, int]]:
    height, width = entropy_map.shape
    coords = [(y, x) for y in range(height) for x in range(width)]
    coords.sort(key=lambda pos: entropy_map[pos[0], pos[1]], reverse=True)
    prng = DeterministicPRNG(seed)
    return prng.shuffle(coords)
