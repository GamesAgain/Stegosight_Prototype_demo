"""Payload reconstruction helpers."""
from __future__ import annotations

import struct
from typing import Tuple

from ..util import bitstream, header
from ..util.header import EncryptedHeader, HEADER_LEN


def parse_plain(bits: list[int]) -> Tuple[bytes, bytes]:
    """Parse a plaintext header and payload from the bitstream."""
    header_bits = bits[: HEADER_LEN * 8]
    header_bytes = bitstream.bits_to_bytes(header_bits)
    payload_length = header.validate_header(header_bytes)
    payload_bits = bits[HEADER_LEN * 8 : HEADER_LEN * 8 + payload_length * 8]
    payload_bytes = bitstream.bits_to_bytes(payload_bits)
    if len(payload_bytes) != payload_length:
        raise ValueError("Insufficient bits to recover payload")
    return header_bytes, payload_bytes


def parse_encrypted(bits: list[int]) -> Tuple[int, EncryptedHeader]:
    """Parse ciphertext length and encrypted header structure."""
    if len(bits) < 32:
        raise ValueError("Insufficient bits to recover encrypted header length")
    length_bytes = bitstream.bits_to_bytes(bits[:32])
    cipher_len = struct.unpack(">I", length_bytes)[0]
    total_bytes = 4 + cipher_len
    total_bits = total_bytes * 8
    if len(bits) < total_bits:
        raise ValueError("Insufficient bits for encrypted payload")
    data_bytes = bitstream.bits_to_bytes(bits[:total_bits])
    payload = data_bytes[4:]

    if cipher_len < 44:
        raise ValueError("Encrypted payload too short to contain metadata")

    salt = payload[:16]
    nonce = payload[16:28]
    tag = payload[28:44]
    ciphertext = payload[44:]
    if len(ciphertext) == 0:
        raise ValueError("Ciphertext missing from encrypted payload")

    encrypted_header = EncryptedHeader(salt=salt, nonce=nonce, tag=tag, ciphertext=ciphertext)
    return total_bits, encrypted_header
