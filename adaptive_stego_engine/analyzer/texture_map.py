"""Texture map aggregator."""
from __future__ import annotations

import numpy as np

from .entropy import compute_entropy
from .gradient import compute_gradient


def compute_texture_maps(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    gray = np.dot(rgb[..., :3], [0.299, 0.587, 0.114]).astype(np.float32)
    gradient_map = compute_gradient(gray)
    entropy_map = compute_entropy(gray)
    surface_map = 0.6 * gradient_map + 0.4 * entropy_map
    surface_map = np.clip(surface_map, 0.0, 1.0)
    return gray, gradient_map, entropy_map, surface_map
