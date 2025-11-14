"""Image loading and saving utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image


def load_png(path: str | Path) -> np.ndarray:
    path = Path(path)
    if path.suffix.lower() != ".png":
        raise ValueError("Only PNG images are supported")
    image = Image.open(path)
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    if image.mode == "RGBA":
        image = image.convert("RGB")
    arr = np.array(image, dtype=np.uint8)
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError("PNG must be 24-bit RGB")
    return arr


def save_png(path: str | Path, data: np.ndarray) -> None:
    path = Path(path)
    if path.suffix.lower() != ".png":
        raise ValueError("Output must be a .png file")
    if data.dtype != np.uint8:
        raise ValueError("Image data must be uint8")
    if data.ndim != 3 or data.shape[2] != 3:
        raise ValueError("Image must be RGB")
    image = Image.fromarray(data, mode="RGB")
    image.save(path, format="PNG")


def image_dimensions(data: np.ndarray) -> Tuple[int, int]:
    if data.ndim != 3 or data.shape[2] != 3:
        raise ValueError("Expected RGB image")
    return data.shape[0], data.shape[1]
