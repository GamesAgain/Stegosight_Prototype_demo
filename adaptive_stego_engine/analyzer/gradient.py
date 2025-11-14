"""Gradient analysis using Sobel filters."""
from __future__ import annotations

import numpy as np
from scipy import ndimage


def sobel_magnitude(image: np.ndarray) -> np.ndarray:
    """Return normalized Sobel gradient magnitude for the image."""
    gray = _to_grayscale(image)
    gx = ndimage.sobel(gray, axis=1, mode="reflect")
    gy = ndimage.sobel(gray, axis=0, mode="reflect")
    magnitude = np.hypot(gx, gy)
    normalized = magnitude / (np.max(magnitude) + 1e-9)
    return normalized.astype(np.float32)


def _to_grayscale(image: np.ndarray) -> np.ndarray:
    if image.ndim == 3 and image.shape[2] == 3:
        return np.dot(image[..., :3], [0.299, 0.587, 0.114])
    if image.ndim == 2:
        return image.astype(np.float32)
    raise ValueError("Unsupported image format for gradient computation")
