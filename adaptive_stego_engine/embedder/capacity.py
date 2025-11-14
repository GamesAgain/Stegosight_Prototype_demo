"""Capacity planning for each pixel based on texture scores and predictors."""
from __future__ import annotations

import numpy as np

from ..analyzer.region_classifier import classify, capacity_map


def pixel_capacity(surface_scores: np.ndarray, predictor_adjustment: np.ndarray | None = None) -> np.ndarray:
    classes = classify(surface_scores)
    capacity = capacity_map(classes).astype(np.int16)
    if predictor_adjustment is not None:
        capacity = np.maximum(0, capacity - predictor_adjustment.astype(np.int16))
    return capacity.astype(np.uint8)


def capacity_to_bit_total(capacity: np.ndarray) -> int:
    return int(np.sum(capacity))
