"""Capacity refinement utilities."""
from __future__ import annotations

import numpy as np


def refine_capacity_map(base_capacity: np.ndarray, surface_map: np.ndarray) -> np.ndarray:
    refined = base_capacity.astype(np.float32)
    refined += surface_map * 0.5
    refined = np.clip(refined, 0, 3)
    return refined.astype(np.int32)
