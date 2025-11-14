"""Bit level helper for extraction pipeline."""
from __future__ import annotations

from typing import Iterable, List


class BitReader:
    def __init__(self, bits: Iterable[int]):
        self._bits: List[int] = list(bits)
        self._index = 0

    def read_bits(self, count: int) -> List[int]:
        if self._index + count > len(self._bits):
            raise ValueError("Not enough bits in stream")
        data = self._bits[self._index:self._index + count]
        self._index += count
        return data

    def read_bytes(self, count: int) -> bytes:
        bits = self.read_bits(count * 8)
        value = 0
        out = bytearray()
        for idx, bit in enumerate(bits):
            value = (value << 1) | (bit & 1)
            if (idx + 1) % 8 == 0:
                out.append(value)
                value = 0
        return bytes(out)

    def remaining_bits(self) -> int:
        return len(self._bits) - self._index
