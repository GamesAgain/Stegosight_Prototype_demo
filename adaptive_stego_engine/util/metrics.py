"""Image quality metrics for adaptive embedding."""
from __future__ import annotations

import math
from typing import Tuple

import numpy as np
from scipy.ndimage import gaussian_filter


def psnr(original: np.ndarray, stego: np.ndarray) -> float:
    mse = np.mean((original.astype(np.float64) - stego.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    max_pixel = 255.0
    return 20 * math.log10(max_pixel / math.sqrt(mse))


def ssim(original: np.ndarray, stego: np.ndarray) -> float:
    original = original.astype(np.float64)
    stego = stego.astype(np.float64)
    K1, K2 = 0.01, 0.03
    L = 255
    C1 = (K1 * L) ** 2
    C2 = (K2 * L) ** 2

    mu1 = gaussian_filter(original, sigma=1.5)
    mu2 = gaussian_filter(stego, sigma=1.5)

    sigma1_sq = gaussian_filter(original ** 2, sigma=1.5) - mu1 ** 2
    sigma2_sq = gaussian_filter(stego ** 2, sigma=1.5) - mu2 ** 2
    sigma12 = gaussian_filter(original * stego, sigma=1.5) - mu1 * mu2

    numerator = (2 * mu1 * mu2 + C1) * (2 * sigma12 + C2)
    denominator = (mu1 ** 2 + mu2 ** 2 + C1) * (sigma1_sq + sigma2_sq + C2)
    ssim_map = numerator / denominator
    return float(np.clip(np.mean(ssim_map), 0.0, 1.0))


def histogram_drift(original: np.ndarray, stego: np.ndarray) -> Tuple[float, float]:
    """Return histogram and variance drift metrics for quality control."""
    if original.shape != stego.shape:
        raise ValueError("Images must share dimensions")
    drift = 0.0
    variance_diff = 0.0
    for channel in range(original.shape[2]):
        hist_orig, _ = np.histogram(original[:, :, channel], bins=256, range=(0, 255), density=True)
        hist_stego, _ = np.histogram(stego[:, :, channel], bins=256, range=(0, 255), density=True)
        drift += float(np.linalg.norm(hist_orig - hist_stego, ord=1))
        variance_diff += float(np.var(stego[:, :, channel]) - np.var(original[:, :, channel]))
    return drift / original.shape[2], variance_diff / original.shape[2]
