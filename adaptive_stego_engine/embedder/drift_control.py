"""Statistical drift control for 8x8 blocks."""
from __future__ import annotations

import numpy as np

from ..util.metrics import block_metrics

BLOCK_SIZE = 8
DRIFT_THRESHOLD = 0.12
VARIANCE_THRESHOLD = 40.0
CHI_SQUARE_THRESHOLD = 120.0


def safe_capacity_mask(image: np.ndarray, capacity: np.ndarray) -> np.ndarray:
    """Return a per-pixel mask (0/1) indicating whether embedding is allowed."""
    mask = np.ones_like(capacity, dtype=np.uint8)
    height, width = capacity.shape
    for y in range(0, height, BLOCK_SIZE):
        for x in range(0, width, BLOCK_SIZE):
            block_capacity = capacity[y:y + BLOCK_SIZE, x:x + BLOCK_SIZE]
            if not block_capacity.any():
                continue
            block = image[y:y + BLOCK_SIZE, x:x + BLOCK_SIZE]
            mean_block = np.full_like(block, np.mean(block))
            drift, var_delta, chi = block_metrics(block, mean_block)
            variance = float(np.var(block))
            if (drift > DRIFT_THRESHOLD or var_delta > VARIANCE_THRESHOLD or chi > CHI_SQUARE_THRESHOLD or variance < 50.0):
                mask[y:y + BLOCK_SIZE, x:x + BLOCK_SIZE] = 0
    return mask


def apply_mask(capacity: np.ndarray, mask: np.ndarray) -> np.ndarray:
    return (capacity * mask).astype(np.uint8)
