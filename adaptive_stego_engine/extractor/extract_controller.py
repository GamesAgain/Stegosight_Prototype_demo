"""High-level extraction controller."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..util.header import EncryptedPackage, decrypt_payload, validate_header
from .bit_reader import BitReader
from .extraction import extract_bits


@dataclass
class ExtractionResult:
    payload: bytes
    encrypted: bool
    mode: str | None


class AdaptiveExtractor:
    def __init__(self, seed: str, password: str | None = None) -> None:
        self.seed = seed
        self.password = password or ""

    def extract(self, image: np.ndarray) -> ExtractionResult:
        bits = extract_bits(image, self.seed)
        reader = BitReader(bits)
        flag = reader.read_bytes(1)
        if not flag:
            raise ValueError("Failed to read encryption flag")
        encrypted = flag[0] == 1
        if not encrypted:
            header_bytes = reader.read_bytes(9)
            payload_length = validate_header(header_bytes)
            payload_bytes = reader.read_bytes(payload_length)
            return ExtractionResult(payload=payload_bytes, encrypted=False, mode=None)

        package_length_bytes = reader.read_bytes(4)
        package_length = int.from_bytes(package_length_bytes, "big")
        if package_length <= 0:
            raise ValueError("Invalid encrypted payload length")
        package_bytes = reader.read_bytes(package_length)
        package = EncryptedPackage.decode(package_bytes)
        try:
            plaintext = decrypt_payload(package, self.password)
        except Exception as exc:  # noqa: BLE001
            raise ValueError("Decryption failed. Check password and mode.") from exc
        header = plaintext[:9]
        payload_length = validate_header(header)
        payload = plaintext[9:9 + payload_length]
        return ExtractionResult(payload=payload, encrypted=True, mode=package.mode)
