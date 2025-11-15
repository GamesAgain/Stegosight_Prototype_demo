"""Capacity planning utilities."""
from __future__ import annotations

import numpy as np

from ..analyzer.region_classifier import EDGE, SMOOTH, TEXTURE


def compute_capacity_map(classification: np.ndarray, surface: np.ndarray) -> np.ndarray:
    """Translate region classification into per-pixel bit capacity."""
    capacity = np.zeros_like(surface, dtype=np.uint8)

    smooth_mask = classification == SMOOTH
    texture_mask = classification == TEXTURE
    edge_mask = classification == EDGE

    capacity[smooth_mask & (surface > 0.12)] = 1
    capacity[texture_mask] = 2
    capacity[edge_mask] = 3

    return capacity
