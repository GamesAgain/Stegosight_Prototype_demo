"""Combine gradient and entropy into a surface score map."""
from __future__ import annotations

import numpy as np

from .gradient import sobel_magnitude
from .entropy import local_entropy


def surface_map(image: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    grad = sobel_magnitude(image)
    entropy = local_entropy(image)
    surface = 0.6 * grad + 0.4 * entropy
    surface = np.clip(surface, 0.0, 1.0)
    return surface.astype(np.float32), grad.astype(np.float32), entropy.astype(np.float32)
