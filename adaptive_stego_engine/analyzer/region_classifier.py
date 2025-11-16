"""Region classifier mapping surface score to embedding capacity."""
from __future__ import annotations

import numpy as np


def compute_capacity_map(surface_map: np.ndarray) -> np.ndarray:
    capacity = np.zeros_like(surface_map, dtype=np.int32)
    capacity[surface_map > 0.25] = 1
    capacity[surface_map > 0.65] = 2
    capacity[surface_map > 0.85] = 3
    return capacity
