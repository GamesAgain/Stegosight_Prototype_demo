"""Low-level multi-bit LSB embedding routines."""
from __future__ import annotations

import numpy as np


def embed_bits_into_pixel(pixel: np.ndarray, bits: list[int]) -> np.ndarray:
    """Return a new pixel with its channels modified according to ``bits``."""
    pixel = pixel.copy()
    for channel, bit in enumerate(bits):
        pixel[channel] = (pixel[channel] & ~1) | (bit & 1)
    return pixel


def extract_bits_from_pixel(pixel: np.ndarray, capacity: int) -> list[int]:
    return [int(pixel[channel] & 1) for channel in range(capacity)]
