"""Local entropy computation utilities."""
from __future__ import annotations

import numpy as np
from scipy import ndimage


def _to_grayscale(image: np.ndarray) -> np.ndarray:
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Entropy computation expects an RGB image array")
    r, g, b = image[..., 0], image[..., 1], image[..., 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray.astype(np.uint8)


def local_entropy(image: np.ndarray, window: int = 5) -> np.ndarray:
    """Compute 5x5 local entropy over the image."""
    gray = _to_grayscale(image)

    def entropy_func(values: np.ndarray) -> float:
        hist = np.bincount(values.astype(np.uint8), minlength=256)
        probs = hist / (hist.sum() or 1)
        probs = probs[probs > 0]
        return float(-np.sum(probs * np.log2(probs)))

    footprint = np.ones((window, window), dtype=np.uint8)
    entropy_map = ndimage.generic_filter(
        gray,
        entropy_func,
        footprint=footprint,
        mode="reflect",
    )
    return entropy_map


def normalized_entropy(image: np.ndarray, window: int = 5) -> np.ndarray:
    """Return entropy normalized to [0, 1]."""
    entropy_map = local_entropy(image, window=window)
    normalized = np.clip(entropy_map / np.log2(256), 0.0, 1.0)
    return normalized.astype(np.float64)
