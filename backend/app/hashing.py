"""Registry of supported hash algorithms.

Adding a new algorithm is intentionally a one-line change: register its name
and a function that turns raw bytes into a lowercase hex digest. Everything
else (the API, the cracker, auto-detection by length) reads from this registry,
so MD5 is just the first of many.
"""

from __future__ import annotations

import hashlib
from collections.abc import Callable

# name -> function(bytes) -> hex digest (lowercase)
ALGORITHMS: dict[str, Callable[[bytes], str]] = {
    "md5": lambda b: hashlib.md5(b).hexdigest(),
    "sha1": lambda b: hashlib.sha1(b).hexdigest(),
    "sha224": lambda b: hashlib.sha224(b).hexdigest(),
    "sha256": lambda b: hashlib.sha256(b).hexdigest(),
    "sha384": lambda b: hashlib.sha384(b).hexdigest(),
    "sha512": lambda b: hashlib.sha512(b).hexdigest(),
}

# Hex-digest length -> algorithms that produce that length, used to guess the
# algorithm when the caller doesn't specify one.
LENGTH_TO_ALGORITHMS: dict[int, list[str]] = {}
for _name, _fn in ALGORITHMS.items():
    _length = len(_fn(b""))
    LENGTH_TO_ALGORITHMS.setdefault(_length, []).append(_name)


def supported_algorithms() -> list[str]:
    """Names of every registered algorithm."""
    return list(ALGORITHMS)


def compute(algorithm: str, text: str) -> str:
    """Hash ``text`` (UTF-8) with ``algorithm`` and return a hex digest."""
    fn = ALGORITHMS[algorithm]
    return fn(text.encode("utf-8"))


def detect_algorithms(hash_hex: str) -> list[str]:
    """Best-effort guess of which algorithms could have produced this hash,
    based on its hex length. Returns an empty list if nothing matches."""
    return LENGTH_TO_ALGORITHMS.get(len(hash_hex.strip()), [])
