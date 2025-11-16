"""Local entropy estimation."""
from __future__ import annotations

import numpy as np
from scipy import ndimage


WINDOW_SIZE = 5


def compute_entropy(gray: np.ndarray) -> np.ndarray:
    if gray.ndim != 2:
        raise ValueError("Entropy map requires grayscale image")
    gray = gray.astype(np.uint8)
    entropy_map = np.zeros_like(gray, dtype=np.float32)
    for value in range(256):
        mask = (gray == value).astype(np.float32)
        prob = ndimage.uniform_filter(mask, size=WINDOW_SIZE)
        with np.errstate(divide="ignore", invalid="ignore"):
            term = np.where(prob > 0, -prob * np.log2(prob), 0)
        entropy_map += term
    entropy_map /= np.log2(256)
    entropy_map = np.clip(entropy_map, 0.0, 1.0)
    return entropy_map
