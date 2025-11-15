"""Region classification based on surface scores."""
from __future__ import annotations

import numpy as np

SMOOTH = 0
TEXTURE = 1
EDGE = 2


REGION_LABELS = {
    SMOOTH: "Smooth",
    TEXTURE: "Texture",
    EDGE: "Edge",
}


def classify(surface: np.ndarray) -> np.ndarray:
    """Classify pixels based on adaptive thresholds."""
    classification = np.empty_like(surface, dtype=np.uint8)
    classification[surface <= 0.25] = SMOOTH
    classification[(surface > 0.25) & (surface <= 0.65)] = TEXTURE
    classification[surface > 0.65] = EDGE
    return classification
