"""Combine gradient and entropy maps into a texture surface score."""
from __future__ import annotations

import numpy as np

from .entropy import local_entropy
from .gradient import sobel_gradient


SURFACE_WEIGHTS = (0.6, 0.4)


def surface_score(image: np.ndarray) -> np.ndarray:
    grad = sobel_gradient(image)
    entropy = local_entropy(image)
    combined = SURFACE_WEIGHTS[0] * grad + SURFACE_WEIGHTS[1] * entropy
    return np.clip(combined, 0.0, 1.0)
