"""Gradient computation using Sobel operators."""
from __future__ import annotations

import numpy as np
from scipy import ndimage


def compute_gradient(gray: np.ndarray) -> np.ndarray:
    if gray.ndim != 2:
        raise ValueError("Grayscale image required")
    gx = ndimage.sobel(gray.astype(np.float32), axis=1)
    gy = ndimage.sobel(gray.astype(np.float32), axis=0)
    mag = np.sqrt(gx ** 2 + gy ** 2)
    if mag.max() == 0:
        return np.zeros_like(mag, dtype=np.float32)
    return (mag - mag.min()) / (mag.max() - mag.min() + 1e-9)
