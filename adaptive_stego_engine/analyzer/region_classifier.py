"""Classify each pixel into smooth/texture/edge regions and assign capacities."""
from __future__ import annotations

import numpy as np


SMOOTH_THRESHOLD = 0.25
TEXTURE_THRESHOLD = 0.65


def classify(surface: np.ndarray) -> np.ndarray:
    classes = np.zeros_like(surface, dtype=np.uint8)
    classes[surface <= SMOOTH_THRESHOLD] = 0
    classes[(surface > SMOOTH_THRESHOLD) & (surface <= TEXTURE_THRESHOLD)] = 1
    classes[surface > TEXTURE_THRESHOLD] = 2
    return classes


def capacity_map(classes: np.ndarray) -> np.ndarray:
    capacity = np.zeros_like(classes, dtype=np.uint8)
    capacity[classes == 0] = 1
    capacity[classes == 1] = 2
    capacity[classes == 2] = 3
    return capacity
