"""Quality metrics for adaptive embedding."""
from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter


def compute_psnr(cover: np.ndarray, stego: np.ndarray) -> float:
    cover_f = cover.astype(np.float64)
    stego_f = stego.astype(np.float64)
    mse = np.mean((cover_f - stego_f) ** 2)
    if mse == 0:
        return 99.0
    return 20 * np.log10(255.0 / np.sqrt(mse))


def _ssim_per_channel(x: np.ndarray, y: np.ndarray) -> float:
    x = x.astype(np.float64)
    y = y.astype(np.float64)
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    mu_x = gaussian_filter(x, sigma=1.5)
    mu_y = gaussian_filter(y, sigma=1.5)
    sigma_x = gaussian_filter(x * x, sigma=1.5) - mu_x ** 2
    sigma_y = gaussian_filter(y * y, sigma=1.5) - mu_y ** 2
    sigma_xy = gaussian_filter(x * y, sigma=1.5) - mu_x * mu_y
    numerator = (2 * mu_x * mu_y + c1) * (2 * sigma_xy + c2)
    denominator = (mu_x ** 2 + mu_y ** 2 + c1) * (sigma_x + sigma_y + c2)
    ssim_map = numerator / (denominator + 1e-12)
    return float(np.mean(ssim_map))


def compute_ssim(cover: np.ndarray, stego: np.ndarray) -> float:
    if cover.shape != stego.shape:
        raise ValueError("Images must match for SSIM")
    channels = []
    for c in range(cover.shape[2]):
        channels.append(_ssim_per_channel(cover[..., c], stego[..., c]))
    return float(np.mean(channels))


def histogram_drift(cover: np.ndarray, stego: np.ndarray) -> float:
    cover_hist = np.histogram(cover, bins=256, range=(0, 255))[0]
    stego_hist = np.histogram(stego, bins=256, range=(0, 255))[0]
    diff = np.abs(cover_hist - stego_hist)
    return float(np.sum(diff) / (cover.size))
