"""Local entropy analysis."""
from __future__ import annotations

import numpy as np
from scipy.ndimage import generic_filter


WINDOW_SIZE = 5


def _entropy_filter(values: np.ndarray) -> float:
    hist, _ = np.histogram(values, bins=16, range=(0, 255), density=True)
    hist = hist[hist > 0]
    if hist.size == 0:
        return 0.0
    return float(-np.sum(hist * np.log2(hist)))


def local_entropy(image: np.ndarray, window: int = WINDOW_SIZE) -> np.ndarray:
    if image.ndim == 3:
        gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
    else:
        gray = image.astype(np.float64)
    entropy_map = generic_filter(gray, _entropy_filter, size=window, mode="reflect")
    entropy_map -= entropy_map.min()
    if entropy_map.max() > 0:
        entropy_map /= entropy_map.max()
    return entropy_map.astype(np.float64)
