"""Image IO helpers with strict PNG validation."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Tuple

import numpy as np
from PIL import Image

from .exceptions import StegoEngineError


PNG_MODE = "PNG"
RGB_MODE = "RGB"


def _validate_png_image(img: Image.Image, path: Path) -> None:
    if img.format != PNG_MODE:
        raise StegoEngineError(f"{path.name} is not a PNG file")
    if img.mode != RGB_MODE:
        raise StegoEngineError("Cover image must be 8-bit RGB PNG")


def load_png(path: str | os.PathLike[str]) -> np.ndarray:
    file_path = Path(path)
    if not file_path.exists():
        raise StegoEngineError(f"Image not found: {file_path}")
    with Image.open(file_path) as img:
        _validate_png_image(img, file_path)
        rgb = np.array(img, dtype=np.uint8)
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise StegoEngineError("PNG must contain exactly three color channels")
    return rgb


def save_png(path: str | os.PathLike[str], rgb: np.ndarray) -> None:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise StegoEngineError("Stego image must be RGB")
    if rgb.dtype != np.uint8:
        raise StegoEngineError("Stego image must be uint8 array")
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.fromarray(rgb, mode=RGB_MODE)
    img.save(file_path, format=PNG_MODE)


def image_dimensions(rgb: np.ndarray) -> Tuple[int, int]:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise StegoEngineError("RGB array expected")
    return int(rgb.shape[0]), int(rgb.shape[1])
