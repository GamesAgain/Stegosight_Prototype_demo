"""Image loading/saving helpers built on top of Pillow."""
from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image


class InvalidImageFormatError(RuntimeError):
    """Raised when a supplied image does not meet the PNG requirement."""


PNG_MODES = {"RGB", "RGBA"}


def load_png(path: str | Path) -> Tuple[np.ndarray, str]:
    """Load a PNG image and return an ``np.uint8`` array and mode string."""
    path = Path(path)
    with Image.open(path) as img:
        if img.format != "PNG":
            raise InvalidImageFormatError("Only 24/32-bit PNG images are supported")
        if img.mode not in PNG_MODES:
            img = img.convert("RGB")
        mode = img.mode
        array = np.array(img, dtype=np.uint8)
    if array.ndim == 2:
        array = np.stack([array] * 3, axis=-1)
        mode = "RGB"
    if array.shape[2] == 4:
        array = array[:, :, :3]
        mode = "RGB"
    return array, mode


def save_png(path: str | Path, array: np.ndarray, mode: str = "RGB") -> None:
    """Save ``array`` as a PNG image preserving the provided ``mode``."""
    path = Path(path)
    image = Image.fromarray(array.astype(np.uint8), mode=mode)
    image.save(path, format="PNG")


def to_uint8(array: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(array), 0, 255).astype(np.uint8)
