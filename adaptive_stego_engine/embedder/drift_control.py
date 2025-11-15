"""Statistical drift control for adaptive embedding."""
from __future__ import annotations

import numpy as np


def histogram_drift(original: np.ndarray, modified: np.ndarray) -> float:
    """Return normalized histogram drift between two RGB blocks."""
    orig_hist, _ = np.histogram(original, bins=256, range=(0, 255))
    mod_hist, _ = np.histogram(modified, bins=256, range=(0, 255))
    total = original.size or 1
    diff = np.sum(np.abs(orig_hist - mod_hist)) / total
    return float(diff)


def variance_ratio(original: np.ndarray, modified: np.ndarray) -> float:
    """Return the ratio of local variance after embedding."""
    orig_var = float(np.var(original)) or 1e-6
    mod_var = float(np.var(modified))
    return mod_var / orig_var


def chi_square_statistic(original: np.ndarray, modified: np.ndarray) -> float:
    """Compute Pearson chi-square statistic between histograms."""
    orig_hist, _ = np.histogram(original, bins=64, range=(0, 255))
    mod_hist, _ = np.histogram(modified, bins=64, range=(0, 255))
    mask = orig_hist > 0
    expected = orig_hist[mask]
    observed = mod_hist[mask]
    chi = np.sum(((observed - expected) ** 2) / expected)
    return float(chi)


def block_safe(original: np.ndarray, modified: np.ndarray) -> bool:
    """Assess whether a modified block passes drift control checks."""
    hist = histogram_drift(original, modified)
    var_ratio = variance_ratio(original, modified)
    chi = chi_square_statistic(original, modified)

    if hist > 0.18:
        return False
    if not (0.5 <= var_ratio <= 1.8):
        return False
    if chi > 450.0:
        return False
    return True
