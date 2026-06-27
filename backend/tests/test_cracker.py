import hashlib

from app import cracker, hashing

# Small fixed wordlist so tests are fast and don't depend on whether the large
# rockyou.txt has been downloaded.
WORDS = ["123456", "qwerty", "hello123", "dragon", "letmein"]


def test_md5_crack_from_wordlist():
    target = hashlib.md5(b"hello123").hexdigest()
    result = cracker.crack(target, algorithm="md5", wordlist=WORDS)
    assert result.found
    assert result.password == "hello123"
    assert result.algorithm == "md5"
    assert result.wordlist == "custom"


def test_auto_detect_md5_by_length():
    target = hashlib.md5(b"qwerty").hexdigest()
    result = cracker.crack(target, wordlist=WORDS)  # no algorithm passed
    assert result.found
    assert result.password == "qwerty"
    assert result.algorithm == "md5"


def test_sha256_crack():
    target = hashlib.sha256(b"dragon").hexdigest()
    result = cracker.crack(target, algorithm="sha256", wordlist=WORDS)
    assert result.found
    assert result.password == "dragon"


def test_not_found_exhausts_wordlist():
    target = hashlib.md5(b"this-is-not-in-the-list-xyz").hexdigest()
    result = cracker.crack(target, algorithm="md5", wordlist=WORDS)
    assert not result.found
    assert result.password is None
    assert result.wordlist_exhausted


def test_invalid_hash_raises():
    try:
        cracker.crack("not-hex!", algorithm="md5", wordlist=WORDS)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for non-hex input")


def test_registry_lengths():
    assert hashing.detect_algorithms("a" * 32) == ["md5"]
    assert "sha256" in hashing.detect_algorithms("a" * 64)


def test_default_wordlist_exists():
    # Either rockyou.txt (if fetched) or common.txt must be available.
    assert cracker.default_wordlist().exists()
