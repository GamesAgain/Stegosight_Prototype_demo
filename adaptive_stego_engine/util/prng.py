"""Deterministic PRNG helpers used to build pixel ordering."""
from __future__ import annotations

import hashlib
from typing import Iterable

import numpy as np


def _seed_from_string(seed: str) -> int:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def shuffle_indices(indices: Iterable[int], seed: str) -> np.ndarray:
    arr = np.array(list(indices), dtype=np.int64)
    rng = np.random.default_rng(_seed_from_string(seed))
    rng.shuffle(arr)
    return arr


def random_state(seed: str) -> np.random.Generator:
    return np.random.default_rng(_seed_from_string(seed))
