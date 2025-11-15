"""High level embedding controller orchestrating the adaptive pipeline."""
from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

from ..analyzer.region_classifier import classify
from ..analyzer.texture_map import compute_surface_score
from ..util import bitstream, header, metrics, prng
from ..util.image_io import image_dimensions
from . import capacity as capacity_module
from . import embedding, noise_predictor, pixel_order
from .drift_control import block_safe


@dataclass
class EmbeddingResult:
    image: np.ndarray
    metrics: Dict[str, float]
    bits_embedded: int
    capacity_bits: int
    encryption: bool


def _prepare_payload_bytes(
    payload_text: str, seed: str, enable_encryption: bool
) -> Tuple[bytes, bool]:
    payload_bytes = payload_text.encode("utf-8")
    plain_header = header.build_plain_header(len(payload_bytes))

    if not enable_encryption:
        return plain_header + payload_bytes, False

    encrypted = header.encrypt_header(seed, plain_header, payload_bytes)
    total_cipher_len = len(encrypted.salt) + len(encrypted.nonce) + len(encrypted.tag) + len(encrypted.ciphertext)
    combined = struct.pack(">I", total_cipher_len)
    combined += encrypted.salt + encrypted.nonce + encrypted.tag + encrypted.ciphertext
    return combined, True


def _simulate_block_capacity(
    base_image: np.ndarray,
    capacities: np.ndarray,
    block_indices: List[Tuple[int, int]],
    by: int,
    bx: int,
    seed: str,
    block_size: int = 8,
) -> None:
    if not block_indices:
        return

    y_end = min(by + block_size, base_image.shape[0])
    x_end = min(bx + block_size, base_image.shape[1])
    base_block = base_image[by:y_end, bx:x_end]
    block_cap = capacities[by:y_end, bx:x_end]

    while True:
        rng = prng.random_state(f"{seed}:{by}:{bx}")
        simulated = base_block.copy()
        for y, x in block_indices:
            if y >= y_end or x >= x_end:
                continue
            rel_y = y - by
            rel_x = x - bx
            cap = int(block_cap[rel_y, rel_x])
            if cap <= 0:
                continue
            for channel in range(cap):
                bit = rng.getrandbits(1)
                channel_idx = channel % 3
                simulated[rel_y, rel_x, channel_idx] = (
                    simulated[rel_y, rel_x, channel_idx] & ~1
                ) | bit
        if block_safe(base_block, simulated):
            break
        if not np.any(block_cap):
            break
        block_cap[:] = np.maximum(block_cap - 1, 0)

    capacities[by:y_end, bx:x_end] = block_cap


def embed_payload(
    cover_image: np.ndarray,
    payload_text: str,
    seed: str,
    enable_encryption: bool,
) -> EmbeddingResult:
    if cover_image.ndim != 3 or cover_image.shape[2] != 3:
        raise ValueError("Cover image must be an RGB array")

    cover = np.ascontiguousarray(cover_image, dtype=np.uint8)
    height, width = image_dimensions(cover)

    _gradient_map, entropy_map, surface_map = compute_surface_score(cover)
    classification = classify(surface_map)
    base_capacity = capacity_module.compute_capacity_map(classification, surface_map)
    adjusted_capacity = noise_predictor.adjust_capacity(cover, base_capacity)

    order = pixel_order.compute_pixel_order(entropy_map, seed)
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

    # Predictive drift control using base cover with cleared LSBs
    base_simulation = cover & 0xFE
    for by, bx in block_sequence:
        _simulate_block_capacity(base_simulation, adjusted_capacity, block_map[(by, bx)], by, bx, seed, block_size)

    capacity_bits = int(adjusted_capacity.sum())

    payload_bytes, encrypted = _prepare_payload_bytes(payload_text, seed, enable_encryption)
    bits = bitstream.bytes_to_bits(payload_bytes)

    if len(bits) > capacity_bits:
        raise ValueError(
            f"Payload requires {len(bits)} bits but capacity is {capacity_bits}."
        )

    stego = cover.copy()
    bit_index = 0

    for by, bx in block_sequence:
        if bit_index >= len(bits):
            break
        block_indices = block_map[(by, bx)]
        bit_index, _ = embedding.embed_bits(
            stego,
            block_indices,
            adjusted_capacity,
            bits,
            bit_index,
        )

    if bit_index < len(bits):
        raise ValueError("Insufficient embedding capacity after drift control adjustments")

    psnr_value = metrics.psnr(cover, stego)
    ssim_value = metrics.ssim(cover, stego)

    if psnr_value < 48.0 or ssim_value < 0.985:
        raise ValueError(
            f"Quality thresholds not met: PSNR={psnr_value:.2f} dB, SSIM={ssim_value:.4f}."
        )

    result_metrics = {
        "psnr": psnr_value,
        "ssim": ssim_value,
        "histogram_drift": metrics.histogram_drift(cover, stego),
    }

    return EmbeddingResult(
        image=stego,
        metrics=result_metrics,
        bits_embedded=len(bits),
        capacity_bits=capacity_bits,
        encryption=encrypted,
    )
