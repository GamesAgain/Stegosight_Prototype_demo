"""Bitstream helpers for LSB embedding."""
from __future__ import annotations

from typing import Iterable, List, Sequence


def bytes_to_bits(data: bytes) -> List[int]:
    """Expand bytes into a list of bits (MSB first)."""
    bits: List[int] = []
    for byte in data:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits


def bits_to_bytes(bits: Sequence[int]) -> bytes:
    """Pack a bit sequence into bytes (MSB first)."""
    if not bits:
        return b""
    padded = list(bits)
    while len(padded) % 8:
        padded.append(0)

    out = bytearray()
    for idx in range(0, len(padded), 8):
        byte = 0
        for shift, bit in enumerate(padded[idx : idx + 8]):
            byte |= (int(bit) & 1) << (7 - shift)
        out.append(byte)
    return bytes(out)


def pack_bitstream(segments: Sequence[bytes]) -> List[int]:
    """Convert multiple byte segments into a single bit list."""
    bits: List[int] = []
    for segment in segments:
        bits.extend(bytes_to_bits(segment))
    return bits


def unpack_bitstream(bits: Sequence[int], length_bytes: int) -> bytes:
    """Convert a subset of bits back into bytes."""
    relevant = bits[: length_bytes * 8]
    return bits_to_bytes(relevant)
