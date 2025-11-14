"""Local entropy estimation for adaptive embedding."""
from __future__ import annotations

import numpy as np
from scipy import ndimage


def local_entropy(image: np.ndarray, window: int = 5) -> np.ndarray:
    gray = _to_grayscale(image)
    footprint = np.ones((window, window))
    hist_range = (0, 255)

    def entropy_func(block: np.ndarray) -> float:
        hist, _ = np.histogram(block, bins=16, range=hist_range, density=True)
        hist = hist[hist > 0]
        return float(-np.sum(hist * np.log2(hist + 1e-12)))

    entropy = ndimage.generic_filter(gray, entropy_func, size=window, mode="reflect")
    entropy = entropy - np.min(entropy)
    entropy /= np.max(entropy) + 1e-9
    return entropy.astype(np.float32)


def _to_grayscale(image: np.ndarray) -> np.ndarray:
    if image.ndim == 3 and image.shape[2] == 3:
        return np.dot(image[..., :3], [0.299, 0.587, 0.114])
    if image.ndim == 2:
        return image.astype(np.float32)
    raise ValueError("Unsupported image format for entropy computation")
