"""Deterministic PRNG helpers for reproducible pixel ordering."""
from __future__ import annotations

import hashlib
import random
from typing import MutableSequence


def _seed_to_int(seed: str) -> int:
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    return int.from_bytes(digest, "big")


def deterministic_shuffle(sequence: MutableSequence, seed: str) -> None:
    """Shuffle a mutable sequence using a deterministic PRNG."""
    rng = random.Random(_seed_to_int(seed))
    rng.shuffle(sequence)


def random_bytes(length: int, seed: str) -> bytes:
    """Generate reproducible pseudo-random bytes from a seed."""
    rng = random.Random(_seed_to_int(seed))
    return bytes(rng.getrandbits(8) for _ in range(length))


def random_state(seed: str) -> random.Random:
    """Return a deterministic random number generator from the seed."""
    return random.Random(_seed_to_int(seed))
