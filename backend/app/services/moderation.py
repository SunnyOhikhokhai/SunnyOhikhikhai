"""Automatic language filter for community posts and public profile fields.

Text and terms are normalised the same way before matching, so common
disguises are caught: case, leetspeak (1d10t, $h1t), repeated letters
(iiidiot), and letters split by spaces or symbols (f.u.c.k, s t u p i d).
Matching is on whole words, so "Scunthorpe"-style false positives are avoided.
"""

from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import BlockedTerm

LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b", "@": "a", "$": "s"})
_REPEATS = re.compile(r"(.)\1+")
_NON_WORD = re.compile(r"[^a-z\s]+")
# Runs of single letters split by spaces or punctuation: "f.u.c.k", "s t u p i d"
_SPACED = re.compile(r"(?<![a-z])(?:[a-z][\s.\-_*+~'`]+){2,}[a-z](?![a-z])")
# Letters with symbols inside a word: "st*pid", "f#ck" -> kept as a wildcard
_MASKED = re.compile(r"[a-z]+[*#%]+[a-z*#%]*")


def normalise(text: str) -> str:
    t = text.lower().translate(LEET)
    t = _SPACED.sub(lambda m: re.sub(r"[^a-z]", "", m.group(0)), t)
    t = _NON_WORD.sub(" ", t)
    t = _REPEATS.sub(r"\1", t)
    return " ".join(t.split())


@dataclass
class ScanResult:
    blocked: list[str]
    review: list[str]

    @property
    def clean(self) -> bool:
        return not self.blocked and not self.review


class _TermCache:
    """Compiled patterns, refreshed at most every 60s or when terms change."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._loaded_at = 0.0
        self._patterns: list[tuple[str, str, re.Pattern, re.Pattern | None]] = []

    def invalidate(self) -> None:
        self._loaded_at = 0.0

    def patterns(self, db: Session):
        with self._lock:
            if time.monotonic() - self._loaded_at > 60:
                rows = db.execute(
                    select(BlockedTerm.term, BlockedTerm.severity).where(BlockedTerm.is_active.is_(True))
                ).all()
                compiled = []
                for term, severity in rows:
                    n = normalise(term)
                    if not n:
                        continue
                    pat = re.compile(rf"(?<![a-z]){re.escape(n)}(?![a-z])")
                    # Masked variant: allow any single masked letter, e.g. st*pid
                    masked = None
                    if " " not in n and len(n) >= 4:
                        masked = re.compile(
                            "(?<![a-z*#%])"
                            + "".join(f"(?:{re.escape(c)}|[*#%])" for c in n)
                            + "(?![a-z*#%])"
                        )
                    compiled.append((term, severity, pat, masked))
                self._patterns = compiled
                self._loaded_at = time.monotonic()
            return self._patterns


cache = _TermCache()


def scan(db: Session, *texts: str | None) -> ScanResult:
    joined = "\n".join(t for t in texts if t)
    norm = normalise(joined)
    raw = _REPEATS.sub(r"\1", joined.lower().translate(LEET))
    blocked: list[str] = []
    review: list[str] = []
    for term, severity, pat, masked in cache.patterns(db):
        hit = pat.search(norm) or (masked is not None and any(masked.fullmatch(w) for w in _MASKED.findall(raw)))
        if hit:
            (blocked if severity == "block" else review).append(term)
    return ScanResult(blocked=blocked, review=review)


# Starter list. Admins can add local-language terms, slurs and phrases from the
# Moderation page; keeping them in the database avoids redeploying to update.
DEFAULT_TERMS: list[tuple[str, str, str]] = [
    # Profanity
    ("fuck", "block", "profanity"),
    ("fucking", "block", "profanity"),
    ("motherfucker", "block", "profanity"),
    ("shit", "block", "profanity"),
    ("bullshit", "block", "profanity"),
    ("bitch", "block", "profanity"),
    ("bastard", "block", "profanity"),
    ("asshole", "block", "profanity"),
    ("dickhead", "block", "profanity"),
    ("cunt", "block", "profanity"),
    ("whore", "block", "profanity"),
    ("slut", "block", "profanity"),
    # Insults (English)
    ("idiot", "block", "insult"),
    ("stupid", "block", "insult"),
    ("imbecile", "block", "insult"),
    ("moron", "block", "insult"),
    ("fool", "block", "insult"),
    ("dumb", "block", "insult"),
    ("useless man", "block", "insult"),
    ("useless woman", "block", "insult"),
    ("shut up", "review", "insult"),
    ("nonsense", "review", "insult"),
    ("rubbish", "review", "insult"),
    # Insults (Nigerian Pidgin / local)
    ("mumu", "block", "insult"),
    ("werey", "block", "insult"),
    ("olodo", "block", "insult"),
    ("ashawo", "block", "insult"),
    ("oloriburuku", "block", "insult"),
    ("ewu", "review", "insult"),
    ("ode", "review", "insult"),
    ("yeye", "review", "insult"),
    ("ole", "review", "insult"),
    # Hate / exclusion (non-indigene residents are the community's core)
    ("go back to your village", "block", "hate"),
    ("go back to your state", "block", "hate"),
    ("go back to where you came from", "block", "hate"),
    ("you people are not from here", "block", "hate"),
    ("tribalist", "review", "hate"),
    ("tribalism", "review", "hate"),
    # Threats
    ("i will kill you", "block", "threat"),
    ("we will kill", "block", "threat"),
    ("burn their houses", "block", "threat"),
    ("wipe them out", "block", "threat"),
]


def seed_default_terms(db: Session) -> None:
    existing = {t.lower() for t in db.scalars(select(BlockedTerm.term)).all()}
    for term, severity, category in DEFAULT_TERMS:
        if term not in existing:
            db.add(BlockedTerm(term=term, severity=severity, category=category))
    db.commit()
    cache.invalidate()
