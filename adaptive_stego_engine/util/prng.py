"""Deterministic pseudo-random number utilities."""
from __future__ import annotations

import hashlib
import random
from typing import List, Sequence, Tuple, TypeVar


def _seed_to_int(seed: str | bytes) -> int:
    if isinstance(seed, str):
        seed_bytes = seed.encode("utf-8")
    else:
        seed_bytes = seed
    digest = hashlib.sha256(seed_bytes).digest()
    return int.from_bytes(digest, "big")


T = TypeVar("T")


def deterministic_shuffle(indices: Sequence[T], seed: str | bytes) -> List[T]:
    """Shuffle a sequence deterministically using a seed."""
    rnd = random.Random(_seed_to_int(seed))
    shuffled = list(indices)
    rnd.shuffle(shuffled)
    return shuffled


def deterministic_permutation(length: int, seed: str | bytes) -> List[int]:
    """Return a deterministic permutation of range(length)."""
    rnd = random.Random(_seed_to_int(seed))
    perm = list(range(length))
    rnd.shuffle(perm)
    return perm


def random_stream(seed: str | bytes) -> random.Random:
    """Return a Random instance seeded deterministically."""
    return random.Random(_seed_to_int(seed))
