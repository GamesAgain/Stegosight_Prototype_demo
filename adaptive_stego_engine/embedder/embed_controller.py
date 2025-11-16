"""High level embedding controller orchestrating the adaptive pipeline."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from ..analyzer.region_classifier import compute_capacity_map
from ..analyzer.texture_map import compute_texture_maps
from ..util import bitstream, header
from ..util.asym_crypto import fingerprint_public_key, load_public_key_pem, rsa_encrypt_key
from ..util.crypto import PBKDF2_SALT_LEN, aes_gcm_encrypt, derive_key_pbkdf2
from ..util.exceptions import StegoEngineError
from ..util.image_io import load_png
from ..util.metrics import compute_psnr, compute_ssim, histogram_drift
from . import capacity as capacity_module
from .embedding import embed_bits_low_level
from .noise_predictor import adjust_capacity_for_pixel
from .pixel_order import build_pixel_order
from .drift_control import BLOCK_SIZE, block_safety_checker


@dataclass
class EmbedMetrics:
    psnr: float
    ssim: float
    hist_drift: float


class EmbedController:
    def __init__(self) -> None:
        pass

    def _build_block_maps(self, height: int, width: int) -> Tuple[np.ndarray, np.ndarray, dict[int, List[int]]]:
        block_rows = (height + BLOCK_SIZE - 1) // BLOCK_SIZE
        block_cols = (width + BLOCK_SIZE - 1) // BLOCK_SIZE
        num_blocks = block_rows * block_cols
        block_map = np.zeros(height * width, dtype=np.int32)
        block_pixel_positions: dict[int, List[int]] = {i: [] for i in range(num_blocks)}
        for idx in range(height * width):
            y = idx // width
            x = idx % width
            block_y = y // BLOCK_SIZE
            block_x = x // BLOCK_SIZE
            block_id = block_y * block_cols + block_x
            block_map[idx] = block_id
            block_pixel_positions[block_id].append(idx)
        block_done = np.zeros(num_blocks, dtype=bool)
        return block_map, block_done, block_pixel_positions

    def _build_symmetric_stream(
        self,
        payload_text: str,
        password: str,
        aes_enabled: bool,
    ) -> Tuple[bytes, str]:
        if not password:
            raise StegoEngineError("Password is required for symmetric mode")
        payload_bytes = payload_text.encode("utf-8")
        plain_header = header.build_plain_header(len(payload_bytes))
        salt = os.urandom(PBKDF2_SALT_LEN)
        key = derive_key_pbkdf2(password, salt)
        hdr_nonce, hdr_ct = header.encrypt_header(plain_header, key)
        if len(hdr_ct) != len(plain_header) + 16:
            raise StegoEngineError("Header encryption failed")
        payload_encrypted = False
        payload_nonce: Optional[bytes] = None
        payload_segment = payload_bytes
        if aes_enabled:
            payload_encrypted = True
            payload_nonce, payload_segment = aes_gcm_encrypt(key, payload_bytes)
        stream = bitstream.pack_symmetric_stream(
            salt=salt,
            header_nonce=hdr_nonce,
            header_ct=hdr_ct,
            payload_bytes=payload_segment,
            payload_encrypted=payload_encrypted,
            payload_nonce=payload_nonce,
        )
        seed = f"sym:{password}"
        return stream, seed

    def _build_public_stream(self, payload_text: str, public_key_path: str) -> Tuple[bytes, str]:
        if not public_key_path:
            raise StegoEngineError("Public key is required for asymmetric mode")
        payload_bytes = payload_text.encode("utf-8")
        plain_header = header.build_plain_header(len(payload_bytes))
        public_key = load_public_key_pem(public_key_path)
        fingerprint = fingerprint_public_key(public_key)
        session_key = os.urandom(32)
        plaintext = plain_header + payload_bytes
        aes_nonce, aes_cipher = aes_gcm_encrypt(session_key, plaintext)
        ek = rsa_encrypt_key(public_key, session_key)
        stream = bitstream.pack_public_stream(ek=ek, aes_nonce=aes_nonce, aes_ct=aes_cipher)
        seed = f"asym:{fingerprint}"
        return stream, seed

    def embed_from_text(
        self,
        cover_path: str,
        secret_text: str,
        mode: str,
        password: Optional[str] = None,
        aes_enabled: bool = False,
        public_key_path: Optional[str] = None,
        show_progress: bool = False,
    ) -> Tuple[np.ndarray, EmbedMetrics]:
        rgb = load_png(cover_path)
        gray, gradient_map, entropy_map, surface_map = compute_texture_maps(rgb)
        base_capacity = compute_capacity_map(surface_map)
        refined_capacity = capacity_module.refine_capacity_map(base_capacity, surface_map)
        capacity_flat = refined_capacity.reshape(-1)

        if mode == "password":
            stream_bytes, seed = self._build_symmetric_stream(secret_text, password or "", aes_enabled)
        elif mode == "public":
            stream_bytes, seed = self._build_public_stream(secret_text, public_key_path or "")
        else:
            raise StegoEngineError("Unsupported mode selected")

        bits = bitstream.bytes_to_bits(stream_bytes)
        if len(bits) == 0:
            raise StegoEngineError("Payload is empty")

        order = build_pixel_order(entropy_map, seed)
        height, width, _ = rgb.shape
        block_map, block_done, block_pixel_positions = self._build_block_maps(height, width)

        stego = embed_bits_low_level(
            rgb,
            order,
            capacity_flat,
            bits,
            block_map,
            block_done,
            block_pixel_positions,
            gray,
            adjust_capacity_for_pixel,
            block_safety_checker,
        )

        psnr_value = compute_psnr(rgb, stego)
        ssim_value = compute_ssim(rgb, stego)
        hist_value = histogram_drift(rgb, stego)
        if psnr_value < 48.0 or ssim_value < 0.985 or hist_value > 0.02:
            raise StegoEngineError(
                f"Quality thresholds not met: PSNR={psnr_value:.2f}, SSIM={ssim_value:.4f}, drift={hist_value:.4f}"
            )
        metrics = EmbedMetrics(psnr=psnr_value, ssim=ssim_value, hist_drift=hist_value)
        return stego, metrics
