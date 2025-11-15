"""Predictive noise correction to adapt capacity per pixel."""
from __future__ import annotations

import numpy as np
from scipy import ndimage


NEIGHBOR_KERNEL = np.array(
    [
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, 1],
    ],
    dtype=np.float64,
)


def adjust_capacity(image: np.ndarray, capacity: np.ndarray) -> np.ndarray:
    """Reduce capacity for pixels that deviate strongly from their neighborhood."""
    grayscale = image.mean(axis=2).astype(np.float64)
    neighbor_sum = ndimage.convolve(grayscale, NEIGHBOR_KERNEL, mode="reflect")
    neighbor_mean = neighbor_sum / NEIGHBOR_KERNEL.sum()

    deviation = np.abs(grayscale - neighbor_mean)
    adjusted = capacity.astype(np.int16).copy()

    adjusted[deviation > 60] = np.maximum(adjusted[deviation > 60] - 2, 0)
    adjusted[(deviation > 30) & (deviation <= 60)] = np.maximum(
        adjusted[(deviation > 30) & (deviation <= 60)] - 1,
        0,
    )

    return adjusted.astype(np.uint8)
