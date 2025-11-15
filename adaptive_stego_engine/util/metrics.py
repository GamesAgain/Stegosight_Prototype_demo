"""Image quality metrics for adaptive embedding validation."""
from __future__ import annotations

import math

import numpy as np


PIXEL_MAX = 255.0


def psnr(original: np.ndarray, modified: np.ndarray) -> float:
    mse = np.mean((original.astype(np.float64) - modified.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    return 20 * math.log10(PIXEL_MAX / math.sqrt(mse))


def ssim(original: np.ndarray, modified: np.ndarray) -> float:
    x = original.astype(np.float64)
    y = modified.astype(np.float64)

    mu_x = x.mean()
    mu_y = y.mean()
    sigma_x = x.var()
    sigma_y = y.var()
    sigma_xy = ((x - mu_x) * (y - mu_y)).mean()

    c1 = (0.01 * PIXEL_MAX) ** 2
    c2 = (0.03 * PIXEL_MAX) ** 2

    numerator = (2 * mu_x * mu_y + c1) * (2 * sigma_xy + c2)
    denominator = (mu_x ** 2 + mu_y ** 2 + c1) * (sigma_x + sigma_y + c2)
    return float(numerator / denominator)


def histogram_drift(original: np.ndarray, modified: np.ndarray) -> float:
    hist_orig, _ = np.histogram(original, bins=256, range=(0, 255))
    hist_mod, _ = np.histogram(modified, bins=256, range=(0, 255))
    total = original.size or 1
    return float(np.sum(np.abs(hist_orig - hist_mod)) / total)
