"""High level extraction controller to recover payloads."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

from ..analyzer.region_classifier import classify
from ..analyzer.texture_map import compute_surface_score
from ..embedder.embed_controller import _simulate_block_capacity
from ..util import header
from . import bit_reader, extraction


@dataclass
class ExtractionResult:
    payload: str
    bits_read: int


def extract_payload(
    stego_image: np.ndarray,
    seed: str,
    encrypted: bool,
) -> ExtractionResult:
    if stego_image.ndim != 3 or stego_image.shape[2] != 3:
        raise ValueError("Stego image must be an RGB array")

    stego = np.ascontiguousarray(stego_image, dtype=np.uint8)

    _gradient_map, entropy_map, surface_map = compute_surface_score(stego)
    classification = classify(surface_map)

    from ..embedder import capacity as capacity_module, noise_predictor, pixel_order as order_module

    base_capacity = capacity_module.compute_capacity_map(classification, surface_map)
    adjusted_capacity = noise_predictor.adjust_capacity(stego, base_capacity)

    order = order_module.compute_pixel_order(entropy_map, seed)

    block_map: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
    block_sequence: List[Tuple[int, int]] = []
    block_size = 8
    for coord in order:
        by = (coord[0] // block_size) * block_size
        bx = (coord[1] // block_size) * block_size
        key = (by, bx)
        if key not in block_map:
            block_map[key] = []
            block_sequence.append(key)
        block_map[key].append(coord)

    base_simulation = stego & 0xFE
    for by, bx in block_sequence:
        _simulate_block_capacity(base_simulation, adjusted_capacity, block_map[(by, bx)], by, bx, seed, block_size)

    bits = bit_reader.extract_bits(stego, order, adjusted_capacity)

    if encrypted:
        total_bits, encrypted_header = extraction.parse_encrypted(bits)
        decrypted = header.decrypt_header(seed, encrypted_header)
        header_bytes = decrypted[: header.HEADER_LEN]
        payload_length = header.validate_header(header_bytes)
        if len(decrypted) < header.HEADER_LEN + payload_length:
            raise ValueError("Encrypted payload truncated; integrity check failed")
        payload_bytes = decrypted[header.HEADER_LEN : header.HEADER_LEN + payload_length]
        try:
            payload_text = payload_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Failed to decode payload; check password") from exc
        bits_read = total_bits
    else:
        header_bytes, payload_bytes = extraction.parse_plain(bits)
        payload_length = header.validate_header(header_bytes)
        payload_bytes = payload_bytes[:payload_length]
        try:
            payload_text = payload_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("Payload is not valid UTF-8") from exc
        bits_read = (header.HEADER_LEN + payload_length) * 8

    return ExtractionResult(payload=payload_text, bits_read=bits_read)
