"""Image quality metrics used to monitor distortion introduced by embedding."""
from __future__ import annotations

import math
from typing import Tuple

import numpy as np
from scipy import ndimage


def psnr(original: np.ndarray, stego: np.ndarray) -> float:
    mse = np.mean((original.astype(np.float64) - stego.astype(np.float64)) ** 2)
    if mse == 0:
        return float("inf")
    return 20 * math.log10(255.0 / math.sqrt(mse))


def ssim(original: np.ndarray, stego: np.ndarray) -> float:
    """Compute a luminance/contrast/structure SSIM approximation."""
    original = original.astype(np.float64)
    stego = stego.astype(np.float64)
    mu1 = ndimage.uniform_filter(original, size=(5, 5, 1))
    mu2 = ndimage.uniform_filter(stego, size=(5, 5, 1))
    sigma1_sq = ndimage.uniform_filter((original - mu1) ** 2, size=(5, 5, 1))
    sigma2_sq = ndimage.uniform_filter((stego - mu2) ** 2, size=(5, 5, 1))
    sigma12 = ndimage.uniform_filter((original - mu1) * (stego - mu2), size=(5, 5, 1))

    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2

    numerator = (2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)
    denominator = (mu1 ** 2 + mu2 ** 2 + c1) * (sigma1_sq + sigma2_sq + c2)
    score = np.mean(numerator / denominator)
    return float(score)


def histogram_drift(original: np.ndarray, stego: np.ndarray, bins: int = 32) -> float:
    """Return L1 distance between normalized histograms of the two images."""
    hist_o, _ = np.histogram(original.flatten(), bins=bins, range=(0, 255), density=True)
    hist_s, _ = np.histogram(stego.flatten(), bins=bins, range=(0, 255), density=True)
    return float(np.sum(np.abs(hist_o - hist_s)))


def block_metrics(original_block: np.ndarray, stego_block: np.ndarray) -> Tuple[float, float, float]:
    drift = histogram_drift(original_block, stego_block, bins=16)
    var_orig = float(np.var(original_block))
    var_stego = float(np.var(stego_block))
    variance_delta = abs(var_orig - var_stego)
    chi_sq = _chi_square(original_block, stego_block)
    return drift, variance_delta, chi_sq


def _chi_square(original: np.ndarray, stego: np.ndarray) -> float:
    hist_o, _ = np.histogram(original.flatten(), bins=32, range=(0, 255))
    hist_s, _ = np.histogram(stego.flatten(), bins=32, range=(0, 255))
    expected = hist_o + 1e-9
    observed = hist_s + 1e-9
    return float(np.sum(((observed - expected) ** 2) / expected))
