"""Dictionary-based hash cracker.

A hash can't be reversed, so "cracking" means hashing candidate words and
comparing against the target — the same approach hashcat/john use. This module
streams a wordlist and tries each candidate against one or more algorithms.
"""

from __future__ import annotations

import re
import time
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from . import hashing

WORDLIST_DIR = Path(__file__).parent / "wordlists"

# Preferred wordlists, largest/best first. The first one that exists on disk is
# used by default. rockyou (~14M leaked passwords from SecLists) is fetched via
# scripts/fetch_wordlists.sh and isn't committed; common.txt always ships.
WORDLIST_PRIORITY = ["rockyou.txt", "common.txt"]

_HEX_RE = re.compile(r"^[0-9a-f]+$")


def default_wordlist() -> Path:
    """Return the best available wordlist on disk (rockyou if fetched, else
    the small committed starter list)."""
    for name in WORDLIST_PRIORITY:
        path = WORDLIST_DIR / name
        if path.exists():
            return path
    return WORDLIST_DIR / "common.txt"


@dataclass
class CrackResult:
    found: bool
    hash: str
    algorithm: str | None = None
    password: str | None = None
    attempts: int = 0
    duration_ms: float = 0.0
    wordlist_exhausted: bool = True
    wordlist: str | None = None


def normalize_hash(hash_hex: str) -> str:
    """Lowercase and strip a hash; raise ValueError if it isn't hex."""
    cleaned = hash_hex.strip().lower()
    if not cleaned or not _HEX_RE.match(cleaned):
        raise ValueError("hash must be a non-empty hexadecimal string")
    return cleaned


def iter_wordlist(path: Path | None = None) -> Iterator[str]:
    """Yield candidate passwords from a wordlist file, one per line.

    Defaults to the best available wordlist (see ``default_wordlist``).
    """
    if path is None:
        path = default_wordlist()
    with path.open("r", encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            word = line.rstrip("\n\r")
            if word:
                yield word


def crack(
    hash_hex: str,
    algorithm: str | None = None,
    wordlist: Iterable[str] | None = None,
) -> CrackResult:
    """Try to recover the plaintext behind ``hash_hex``.

    If ``algorithm`` is None, it's guessed from the hash length (e.g. a 32-char
    hash is tried as MD5). Returns a CrackResult describing the outcome.
    """
    target = normalize_hash(hash_hex)

    if algorithm is not None:
        if algorithm not in hashing.ALGORITHMS:
            raise ValueError(f"unsupported algorithm: {algorithm!r}")
        algorithms = [algorithm]
    else:
        algorithms = hashing.detect_algorithms(target)
        if not algorithms:
            raise ValueError(
                f"could not auto-detect algorithm for a {len(target)}-char hash; "
                "pass `algorithm` explicitly"
            )

    if wordlist is None:
        candidates: Iterable[str] = iter_wordlist()
        wordlist_name = default_wordlist().name
    else:
        candidates = wordlist
        wordlist_name = "custom"

    attempts = 0
    start = time.perf_counter()
    for word in candidates:
        for algo in algorithms:
            attempts += 1
            if hashing.compute(algo, word) == target:
                return CrackResult(
                    found=True,
                    hash=target,
                    algorithm=algo,
                    password=word,
                    attempts=attempts,
                    duration_ms=(time.perf_counter() - start) * 1000,
                    wordlist_exhausted=False,
                    wordlist=wordlist_name,
                )

    return CrackResult(
        found=False,
        hash=target,
        algorithm=algorithms[0] if len(algorithms) == 1 else None,
        attempts=attempts,
        duration_ms=(time.perf_counter() - start) * 1000,
        wordlist_exhausted=True,
        wordlist=wordlist_name,
    )
