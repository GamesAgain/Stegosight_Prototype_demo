"""Statistical drift monitoring for embedded blocks."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Tuple

import numpy as np


class DriftController:
    def __init__(self, cover: np.ndarray, block_size: int = 8) -> None:
        self.cover = cover
        self.block_size = block_size
        self.failures: Dict[Tuple[int, int], int] = defaultdict(int)
        self.locked_blocks: set[Tuple[int, int]] = set()

    def _block_index(self, y: int, x: int) -> Tuple[int, int]:
        return y // self.block_size, x // self.block_size

    def _extract_block(self, image: np.ndarray, block_idx: Tuple[int, int]) -> np.ndarray:
        by, bx = block_idx
        y0 = by * self.block_size
        x0 = bx * self.block_size
        return image[y0 : y0 + self.block_size, x0 : x0 + self.block_size]

    def validate_change(self, image: np.ndarray, y: int, x: int) -> bool:
        block_idx = self._block_index(y, x)
        if block_idx in self.locked_blocks:
            return False
        cover_block = self._extract_block(self.cover, block_idx)
        stego_block = self._extract_block(image, block_idx)
        # handle edge blocks that may be smaller
        if cover_block.shape != stego_block.shape:
            cover_block = cover_block[: stego_block.shape[0], : stego_block.shape[1]]
        if not self._is_safe(cover_block, stego_block):
            self.failures[block_idx] += 1
            if self.failures[block_idx] >= 3:
                self.locked_blocks.add(block_idx)
            return False
        self.failures[block_idx] = 0
        return True

    @staticmethod
    def _is_safe(cover_block: np.ndarray, stego_block: np.ndarray) -> bool:
        hist_threshold = 0.25
        var_threshold = 75.0
        chi_threshold = 0.004

        cover_hist = []
        stego_hist = []
        for ch in range(cover_block.shape[2]):
            c_hist, _ = np.histogram(cover_block[:, :, ch], bins=64, range=(0, 255), density=True)
            s_hist, _ = np.histogram(stego_block[:, :, ch], bins=64, range=(0, 255), density=True)
            cover_hist.append(c_hist)
            stego_hist.append(s_hist)
        cover_hist = np.array(cover_hist)
        stego_hist = np.array(stego_hist)

        hist_drift = float(np.mean(np.sum(np.abs(cover_hist - stego_hist), axis=1)))
        var_diff = float(np.mean(np.abs(np.var(stego_block, axis=(0, 1)) - np.var(cover_block, axis=(0, 1)))))
        chi_sq = float(np.mean(((stego_hist - cover_hist) ** 2) / (cover_hist + 1e-6)))
        return hist_drift <= hist_threshold and var_diff <= var_threshold and chi_sq <= chi_threshold
