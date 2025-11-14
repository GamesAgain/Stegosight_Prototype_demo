"""Pixel ordering utilities for adaptive embedding."""
from __future__ import annotations

from typing import List, Tuple

import numpy as np

from ..analyzer.entropy import local_entropy
from ..util import prng


PixelIndex = Tuple[int, int, int]


def prioritized_pixel_indices(image: np.ndarray, seed: str) -> List[PixelIndex]:
    """Return pixel indices ordered by entropy with deterministic randomisation.

    The specification requires that pixels are first prioritised by entropy and
    then shuffled deterministically using the seed.  A full shuffle after
    sorting would discard the entropy ordering entirely, so we instead apply a
    deterministic tie-breaker derived from a PRNG stream.  This keeps
    high-entropy pixels at the front of the list while still producing a
    seed-dependent permutation among pixels with comparable entropy values.
    """

    entropy_map = local_entropy(image)
    h, w = entropy_map.shape
    rng = prng.random_stream(seed)

    scored_indices: List[tuple[float, float, PixelIndex]] = []
    for y in range(h):
        for x in range(w):
            entropy_score = float(entropy_map[y, x])
            for channel in range(3):
                tie_breaker = rng.random()
                scored_indices.append((entropy_score, tie_breaker, (y, x, channel)))

    scored_indices.sort(key=lambda item: (-item[0], item[1]))
    return [idx for _, _, idx in scored_indices]
