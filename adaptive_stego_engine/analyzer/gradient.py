"""Gradient analysis utilities."""
from __future__ import annotations

import numpy as np
from scipy import ndimage


def sobel_gradient(image: np.ndarray) -> np.ndarray:
    """Return normalized Sobel gradient magnitude map."""
    if image.ndim == 3:
        gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
    else:
        gray = image.astype(np.float64)
    gx = ndimage.sobel(gray, axis=1, mode="reflect")
    gy = ndimage.sobel(gray, axis=0, mode="reflect")
    mag = np.hypot(gx, gy)
    if np.max(mag) == 0:
        return np.zeros_like(mag, dtype=np.float64)
    mag_norm = (mag - mag.min()) / (mag.max() - mag.min())
    return mag_norm.astype(np.float64)
