"""Bitstream utilities for converting between bytes and bits."""
from __future__ import annotations

from typing import Iterable, List


def bytes_to_bits(data: bytes) -> List[int]:
    """Convert bytes to a list of bits (MSB first)."""
    bits: List[int] = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def bits_to_bytes(bits: Iterable[int]) -> bytes:
    """Convert an iterable of bits (MSB first) to bytes."""
    value = 0
    count = 0
    out = bytearray()
    for bit in bits:
        value = (value << 1) | (bit & 1)
        count += 1
        if count == 8:
            out.append(value)
            value = 0
            count = 0
    if count:
        value <<= 8 - count
        out.append(value)
    return bytes(out)


def pack_bitstream(bit_chunks: Iterable[Iterable[int]]) -> List[int]:
    """Flatten a nested iterable of bits into a single list."""
    packed: List[int] = []
    for chunk in bit_chunks:
        packed.extend(int(bit) & 1 for bit in chunk)
    return packed


def unpack_bitstream(bits: Iterable[int], block_size: int) -> List[List[int]]:
    """Split a bitstream into equally-sized blocks.

    Parameters
    ----------
    bits: Iterable[int]
        Bitstream to chunk.
    block_size: int
        Size of each block.
    """
    if block_size <= 0:
        raise ValueError("block_size must be positive")
    result: List[List[int]] = []
    block: List[int] = []
    for bit in bits:
        block.append(int(bit) & 1)
        if len(block) == block_size:
            result.append(block)
            block = []
    if block:
        result.append(block)
    return result
