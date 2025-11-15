"""PNG IO utilities for 24-bit RGB images."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image


PNG_MODE = "RGB"


def load_png(path: Path) -> np.ndarray:
    """Load a 24-bit PNG image as a NumPy array."""
    with Image.open(path) as img:
        if img.format != "PNG":
            raise ValueError("Only PNG images are supported")
        if img.mode != PNG_MODE:
            raise ValueError("PNG must be 24-bit RGB (no alpha channel)")
        array = np.array(img, dtype=np.uint8)
    return array


def save_png(path: Path, array: np.ndarray) -> None:
    """Save an RGB NumPy array as a PNG file."""
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError("Expected RGB array with shape (H, W, 3)")
    image = Image.fromarray(array.astype(np.uint8), mode=PNG_MODE)
    image.save(path, format="PNG")


def image_dimensions(array: np.ndarray) -> Tuple[int, int]:
    """Return (height, width) for the image array."""
    if array.ndim != 3 or array.shape[2] != 3:
        raise ValueError("Invalid RGB image dimensions")
    return array.shape[0], array.shape[1]
