"""Bitstream utilities for converting between bytes and bit-level representations."""
from __future__ import annotations

from typing import Iterable, List


def bytes_to_bits(data: bytes) -> List[int]:
    """Convert a byte string to a list of bits (MSB first for each byte)."""
    bits: List[int] = []
    for byte in data:
        bits.extend((byte >> shift) & 1 for shift in range(7, -1, -1))
    return bits


def bits_to_bytes(bits: Iterable[int]) -> bytes:
    """Convert an iterable of bits (MSB first) into bytes."""
    output = bytearray()
    current = 0
    count = 0
    for bit in bits:
        current = (current << 1) | (bit & 1)
        count += 1
        if count == 8:
            output.append(current)
            current = 0
            count = 0
    if count:
        current <<= 8 - count
        output.append(current)
    return bytes(output)


def pack_bitstream(bit_segments: Iterable[Iterable[int]]) -> List[int]:
    """Concatenate multiple bit iterables into a single list."""
    packed: List[int] = []
    for segment in bit_segments:
        packed.extend(int(bit) & 1 for bit in segment)
    return packed


def unpack_bitstream(bits: Iterable[int], count: int) -> List[int]:
    """Return the first *count* bits from the iterable as a list."""
    extracted: List[int] = []
    for idx, bit in enumerate(bits):
        if idx >= count:
            break
        extracted.append(int(bit) & 1)
    if len(extracted) < count:
        raise ValueError("Insufficient bits available in stream")
    return extracted
