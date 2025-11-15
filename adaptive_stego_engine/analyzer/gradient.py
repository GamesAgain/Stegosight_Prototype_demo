"""Gradient analysis helpers using Sobel operators."""
from __future__ import annotations

import numpy as np
from scipy import ndimage


def _to_grayscale(image: np.ndarray) -> np.ndarray:
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Sobel gradient expects an RGB image array")
    r, g, b = image[..., 0], image[..., 1], image[..., 2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b
    return gray.astype(np.float64)


def sobel_components(image: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return Sobel gradients along X and Y axes."""
    gray = _to_grayscale(image)
    gx = ndimage.sobel(gray, axis=1, mode="reflect")
    gy = ndimage.sobel(gray, axis=0, mode="reflect")
    return gx, gy


def sobel_magnitude(image: np.ndarray) -> np.ndarray:
    """Compute normalized Sobel magnitude in the range [0, 1]."""
    gx, gy = sobel_components(image)
    magnitude = np.hypot(gx, gy)
    max_val = magnitude.max() or 1.0
    magnitude /= max_val
    return magnitude


def normalized_gradient(image: np.ndarray) -> np.ndarray:
    """Return the normalized Sobel magnitude with contrast stretching."""
    magnitude = sobel_magnitude(image)
    low, high = np.percentile(magnitude, (2, 98))
    if high <= low:
        return np.clip(magnitude, 0.0, 1.0)
    stretched = np.clip((magnitude - low) / (high - low), 0.0, 1.0)
    return stretched
