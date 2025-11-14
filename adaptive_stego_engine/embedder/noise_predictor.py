"""Predictive noise control utilities."""
from __future__ import annotations

import numpy as np


NEIGHBOR_OFFSETS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),          (0, 1),
    (1, -1),  (1, 0), (1, 1),
]


def adaptive_capacity(image: np.ndarray, y: int, x: int, channel: int, desired_bits: int) -> int:
    h, w, _ = image.shape
    neighbors = []
    for dy, dx in NEIGHBOR_OFFSETS:
        ny, nx = y + dy, x + dx
        if 0 <= ny < h and 0 <= nx < w:
            neighbors.append(int(image[ny, nx, channel]))
    if not neighbors:
        return min(desired_bits, 1)
    mean_neighbor = np.mean(neighbors)
    current = int(image[y, x, channel])
    deviation = abs(current - mean_neighbor)
    if deviation > 40:
        return max(1, desired_bits - 2)
    if deviation > 20:
        return max(1, desired_bits - 1)
    return desired_bits
