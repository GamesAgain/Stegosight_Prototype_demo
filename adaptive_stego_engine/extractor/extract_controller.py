"""High level extraction controller."""
from __future__ import annotations

from ..analyzer.region_classifier import compute_capacity_map
from ..analyzer.texture_map import compute_texture_maps
from ..embedder import capacity as capacity_module
from ..embedder.pixel_order import build_pixel_order
from ..util.exceptions import StegoEngineError
from ..util.image_io import load_png
from ..util.asym_crypto import fingerprint_public_key, load_private_key_pem
from .bit_reader import read_payload_asymmetric_from_bits, read_payload_symmetric_from_bits
from .extraction import extract_bits_low_level


class ExtractController:
    def _prepare_maps(self, path: str):
        rgb = load_png(path)
        _gray, _gradient_map, entropy_map, surface_map = compute_texture_maps(rgb)
        base_capacity = compute_capacity_map(surface_map)
        refined_capacity = capacity_module.refine_capacity_map(base_capacity, surface_map)
        return rgb, entropy_map, refined_capacity

    def extract_from_image_symmetric(self, stego_path: str, password: str) -> bytes:
        if not password:
            raise StegoEngineError("Password required for symmetric extraction")
        rgb, entropy_map, capacity_map = self._prepare_maps(stego_path)
        seed = f"sym:{password}"
        order = build_pixel_order(entropy_map, seed)
        bits = extract_bits_low_level(rgb, order, capacity_map.reshape(-1))
        return read_payload_symmetric_from_bits(bits, password)

    def extract_from_image_asymmetric(self, stego_path: str, private_key_path: str) -> bytes:
        if not private_key_path:
            raise StegoEngineError("Private key path is required")
        rgb, entropy_map, capacity_map = self._prepare_maps(stego_path)
        private_key = load_private_key_pem(private_key_path)
        fingerprint = fingerprint_public_key(private_key.public_key())
        seed = f"asym:{fingerprint}"
        order = build_pixel_order(entropy_map, seed)
        bits = extract_bits_low_level(rgb, order, capacity_map.reshape(-1))
        return read_payload_asymmetric_from_bits(bits, private_key_path)

    def extract_from_image(self, stego_path: str, seed: str, aes_enabled: bool) -> bytes:
        # Legacy compatibility wrapper, treat seed as password
        return self.extract_from_image_symmetric(stego_path, seed)
