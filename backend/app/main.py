"""Ruki-Pass backend API.

A small FastAPI service for hash-cracking research. MD5 is the first supported
algorithm; the registry in ``hashing.py`` makes adding more a one-line change.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Literal

from pydantic import BaseModel, Field

from . import cracker, hashing

app = FastAPI(
    title="Ruki-Pass API",
    description="Hash-cracking research API (MD5 and more).",
    version="0.1.0",
)

# Allow the Vite dev server to call us during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CrackRequest(BaseModel):
    hash: str = Field(..., description="The hash to crack, as a hex string.")
    algorithm: str | None = Field(
        None,
        description="Hash algorithm (e.g. 'md5'). Auto-detected from length if omitted.",
    )
    use_rules: bool = Field(
        True,
        description="Apply mutation rules (capitalization, numbers, leet) to base words.",
    )
    extra_words: list[str] = Field(
        default_factory=list,
        description="Extra seed words (e.g. a name) to mutate, like 'mors' -> 'Mors123'.",
    )
    brute_force: bool = Field(
        False,
        description="Brute-force numeric suffixes on the seed words (e.g. 'anup' -> 'anup77353').",
    )
    brute_max_digits: int = Field(
        5,
        ge=1,
        le=8,
        description="Max trailing digits to try when length is unknown.",
    )
    length: int | None = Field(
        None,
        ge=1,
        le=64,
        description="Known total password length — prunes the brute-force search.",
    )
    special: Literal["unknown", "yes", "no"] = Field(
        "unknown",
        description="Whether the password contains a special character.",
    )
    brute_around: bool = Field(
        False,
        description="Also place digits before/around the word ('45akash5465'), not just at the end.",
    )


class CrackResponse(BaseModel):
    found: bool
    hash: str
    algorithm: str | None = None
    password: str | None = None
    attempts: int
    duration_ms: float
    wordlist_exhausted: bool
    wordlist: str | None = None


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/algorithms")
def algorithms() -> dict[str, list[str]]:
    """List every hash algorithm the cracker currently supports."""
    return {"algorithms": hashing.supported_algorithms()}


@app.post("/api/crack", response_model=CrackResponse)
def crack(req: CrackRequest) -> CrackResponse:
    """Attempt to recover the plaintext behind a hash using the wordlist."""
    try:
        result = cracker.crack(
            req.hash,
            algorithm=req.algorithm,
            use_rules=req.use_rules,
            extra_words=req.extra_words,
            brute_force=req.brute_force,
            brute_max_digits=req.brute_max_digits,
            length=req.length,
            special=req.special,
            brute_around=req.brute_around,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return CrackResponse(
        found=result.found,
        hash=result.hash,
        algorithm=result.algorithm,
        password=result.password,
        attempts=result.attempts,
        duration_ms=round(result.duration_ms, 3),
        wordlist_exhausted=result.wordlist_exhausted,
        wordlist=result.wordlist,
    )
