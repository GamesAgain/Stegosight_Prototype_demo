"""Combine gradient and entropy into an adaptive texture map."""
from __future__ import annotations

import numpy as np

from .gradient import normalized_gradient
from .entropy import normalized_entropy


def compute_surface_score(image: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return normalized gradient, entropy and combined surface score."""
    grad = normalized_gradient(image)
    ent = normalized_entropy(image)
    surface = 0.6 * grad + 0.4 * ent
    surface = np.clip(surface, 0.0, 1.0)
    return grad, ent, surface
