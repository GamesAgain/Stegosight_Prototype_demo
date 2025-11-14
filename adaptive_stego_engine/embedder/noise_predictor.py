"""Predictive noise control based on local neighbourhood statistics."""
from __future__ import annotations

import numpy as np
from scipy import ndimage


def predictor_penalty(image: np.ndarray, threshold: float = 30.0) -> np.ndarray:
    """Return per-pixel penalties (0-2) depending on predicted distortion."""
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("Expected RGB image for predictor penalty")
    penalty = np.zeros(image.shape[:2], dtype=np.uint8)
    for channel in range(3):
        channel_data = image[:, :, channel].astype(np.float32)
        neighbor_mean = ndimage.uniform_filter(channel_data, size=3, mode="reflect")
        diff = np.abs(channel_data - neighbor_mean)
        penalty = np.maximum(penalty, np.where(diff > threshold, 1, penalty))
        penalty = np.maximum(penalty, np.where(diff > 2 * threshold, 2, penalty))
    return penalty
