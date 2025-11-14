"""Region classification utilities based on surface score."""
from __future__ import annotations

import numpy as np


class RegionType:
    SMOOTH = 0
    TEXTURE = 1
    EDGE = 2


CAPACITY_TABLE = {
    RegionType.SMOOTH: 1,
    RegionType.TEXTURE: 2,
    RegionType.EDGE: 3,
}


THRESHOLDS = (
    (0.0, 0.25, RegionType.SMOOTH),
    (0.25, 0.66, RegionType.TEXTURE),
    (0.66, 1.01, RegionType.EDGE),
)


def classify(surface: np.ndarray) -> np.ndarray:
    classes = np.zeros_like(surface, dtype=np.uint8)
    for low, high, label in THRESHOLDS:
        mask = (surface >= low) & (surface < high)
        classes[mask] = label
    return classes


def capacity_map(classes: np.ndarray) -> np.ndarray:
    capacity = np.zeros_like(classes, dtype=np.uint8)
    for region, bits in CAPACITY_TABLE.items():
        capacity[classes == region] = bits
    return capacity
