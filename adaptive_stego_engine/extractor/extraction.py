"""Low level extraction helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generator

import numpy as np

from ..embedder import capacity as capacity_module
from ..util.bitstream import bits_to_bytes
from .bit_reader import read_bits


@dataclass
class ExtractedPackage:
    raw_bytes: bytes
    encrypted: bool


class ExtractionError(Exception):
    pass


class BitStreamReader:
    def __init__(self, bit_generator: Generator[int, None, None]):
        self._generator = bit_generator
        self._buffer: list[int] = []

    def read_bits(self, count: int) -> list[int]:
        while len(self._buffer) < count:
            try:
                self._buffer.append(next(self._generator))
            except StopIteration as exc:  # pragma: no cover
                raise ExtractionError("Unexpected end of bitstream") from exc
        result = self._buffer[:count]
        self._buffer = self._buffer[count:]
        return result

    def read_bytes(self, count: int) -> bytes:
        return bits_to_bytes(self.read_bits(count * 8))[:count]


def acquire_bit_reader(stego_image: np.ndarray, seed: str) -> BitStreamReader:
    capacity_map, _ = capacity_module.compute_capacity(stego_image)
    generator = read_bits(stego_image, capacity_map, seed)
    return BitStreamReader(generator)
