"""Capacity planning for adaptive embedding."""
from __future__ import annotations

import numpy as np

from ..analyzer import region_classifier, texture_map


def compute_capacity(image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    surface = texture_map.surface_score(image)
    classes = region_classifier.classify(surface)
    capacity = region_classifier.capacity_map(classes)
    return capacity, classes
