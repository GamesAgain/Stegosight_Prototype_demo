"""Predictive noise correction to adapt capacity per pixel."""
from __future__ import annotations

import numpy as np


NEIGHBOR_KERNEL = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def adjust_capacity_for_pixel(gray: np.ndarray, y: int, x: int, requested_cap: int) -> int:
    h, w = gray.shape
    neighbors = []
    for dy, dx in NEIGHBOR_KERNEL:
        ny, nx = y + dy, x + dx
        if 0 <= ny < h and 0 <= nx < w:
            neighbors.append(gray[ny, nx])
    if not neighbors:
        return min(1, requested_cap)
    mean_neighbor = float(np.mean(neighbors))
    deviation = abs(float(gray[y, x]) - mean_neighbor)
    if deviation < 5:
        return requested_cap
    if deviation < 12:
        return max(1, requested_cap - 1)
    if deviation < 20:
        return max(1, requested_cap - 2)
    return 0
