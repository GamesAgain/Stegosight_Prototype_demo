"""Deterministic pseudo random utilities used to shuffle pixel order."""
from __future__ import annotations

import hashlib
import random
from typing import List, Sequence, Tuple


class DeterministicPRNG:
    """Wrapper around Python's ``random.Random`` seeded deterministically."""

    def __init__(self, seed: str | bytes) -> None:
        if isinstance(seed, str):
            seed_bytes = seed.encode("utf-8")
        else:
            seed_bytes = seed
        digest = hashlib.sha256(seed_bytes).digest()
        seed_int = int.from_bytes(digest, "big")
        self._rng = random.Random(seed_int)

    def shuffle(self, items: Sequence[Tuple[int, int]]) -> List[Tuple[int, int]]:
        result = list(items)
        self._rng.shuffle(result)
        return result

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)


def shuffled_indices(width: int, height: int, seed: str | bytes) -> List[Tuple[int, int]]:
    """Return deterministic shuffled pixel coordinates for the given seed."""
    coords = [(y, x) for y in range(height) for x in range(width)]
    prng = DeterministicPRNG(seed)
    return prng.shuffle(coords)
