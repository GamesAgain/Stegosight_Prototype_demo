"""Block-level drift control helpers."""
from __future__ import annotations

import numpy as np


BLOCK_SIZE = 8


def block_safety_checker(original: np.ndarray, stego: np.ndarray) -> bool:
    if original.size == 0:
        return True
    diff = stego.astype(np.int16) - original.astype(np.int16)
    mse = np.mean(diff ** 2)
    if mse > 4.0:
        return False
    orig_hist = np.histogram(original, bins=16, range=(0, 255))[0]
    stego_hist = np.histogram(stego, bins=16, range=(0, 255))[0]
    drift = np.sum(np.abs(orig_hist - stego_hist)) / original.size
    if drift > 0.25:
        return False
    var_ratio = np.var(stego) / (np.var(original) + 1e-6)
    return 0.75 <= var_ratio <= 1.25
