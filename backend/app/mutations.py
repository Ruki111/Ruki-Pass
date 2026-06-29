"""Rule-based password mutations.

A plain wordlist only finds passwords that are literally in it. Real passwords
are usually a base word plus predictable tweaks: a capital letter, a trailing
number or year, a "!", some leet substitution. This module takes a base word
and yields those variants — the same idea as hashcat rules.

Example: "mors" -> "Mors", "MORS", "mors123", "Mors123", "M0rs", "Mors!", ...
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

# Common things people append to a base word.
SUFFIXES = [
    "", "1", "2", "3", "12", "123", "1234", "12345", "11", "21", "69", "007",
    "777", "00", "01", "99", "!", "!!", "@", "#", "$", "1!", "123!", "321",
    "2019", "2020", "2021", "2022", "2023", "2024", "2025",
]

# Less common, but cheap to also try in front.
PREFIXES = ["", "1", "!", "123"]

# Light leet map — one aggressive "translate everything" pass per base.
_LEET = str.maketrans({"a": "@", "e": "3", "i": "1", "o": "0", "s": "$"})

# Common special characters people stick on a password.
SPECIALS = list("!@#$%&*._-")


def _case_variants(word: str) -> Iterator[str]:
    seen: set[str] = set()
    for v in (word, word.lower(), word.upper(), word.capitalize()):
        if v and v not in seen:
            seen.add(v)
            yield v


def mutate(word: str, leet: bool = True) -> Iterator[str]:
    """Yield rule-based variants of a single base word (de-duplicated)."""
    bases = list(_case_variants(word))
    if leet:
        bases += [b.translate(_LEET) for b in bases]

    seen: set[str] = set()
    for base in bases:
        for prefix in PREFIXES:
            for suffix in SUFFIXES:
                cand = f"{prefix}{base}{suffix}"
                if cand not in seen:
                    seen.add(cand)
                    yield cand


def mutate_all(words: Iterable[str], leet: bool = True) -> Iterator[str]:
    """Yield mutations for every base word in ``words``."""
    for word in words:
        yield from mutate(word, leet)


def _digit_strings(length: int) -> Iterator[str]:
    """Yield every zero-padded number of exactly ``length`` digits
    ('00'..'99' for length=2). Covers arbitrary numeric suffixes like 77353."""
    for n in range(10**length):
        yield str(n).zfill(length)


def _digits_or_empty(n: int) -> Iterator[str]:
    """All ``n``-digit zero-padded strings, or a single '' when n == 0."""
    if n == 0:
        yield ""
    else:
        yield from _digit_strings(n)


def brute_append(
    words: Iterable[str],
    max_digits: int = 5,
    length: int | None = None,
    special: str = "unknown",
    around: bool = False,
) -> Iterator[str]:
    """Smart brute force: yield base word + numeric digits (+ optional special
    char), pruned by what the user knows.

    - ``length``: if set, only candidates of exactly that total length are
      produced — this slashes the search space (the digit count is derived).
    - ``special``: 'no' tries no special char, 'yes' requires one, 'unknown'
      tries both.
    - ``max_digits``: when ``length`` is unknown, how many digits to try.
    - ``around``: also place digits *before* the word and on *both* sides
      ('45' + 'akash' + '5465'), not just as a trailing suffix.

    Examples:
      ['anup'], length=9,  special='no'            -> ...'anup77353'...
      ['akash'], length=11, special='no', around=True -> ...'45akash5465'...
    """
    if special == "no":
        special_choices = [""]
    elif special == "yes":
        special_choices = SPECIALS
    else:  # "unknown"
        special_choices = ["", *SPECIALS]

    for word in words:
        for base in _case_variants(word):
            for sp in special_choices:
                if length is not None:
                    budget = length - len(base) - len(sp)
                    if budget < 0:
                        continue
                    if around:
                        # Split the digit budget between front and back.
                        for front in range(budget + 1):
                            back = budget - front
                            for fd in _digits_or_empty(front):
                                for bd in _digits_or_empty(back):
                                    yield f"{fd}{base}{bd}{sp}"
                    else:
                        for digits in _digits_or_empty(budget):
                            yield f"{base}{digits}{sp}"
                            if sp:
                                yield f"{base}{sp}{digits}"
                else:
                    for dlen in range(max_digits + 1):
                        for digits in _digits_or_empty(dlen):
                            # suffix is the most common shape; with `around`,
                            # also try the digits as a prefix.
                            yield f"{base}{digits}{sp}"
                            if around and digits:
                                yield f"{digits}{base}{sp}"
                            if sp and digits:
                                yield f"{base}{sp}{digits}"
