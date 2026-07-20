"""Intent embedding. Default is a dependency-free hashed n-gram embedder
(ADR-0004); plug in a real semantic embedder via the Embedder protocol."""

from __future__ import annotations

import math
import re
import zlib
from typing import Protocol

WORD_WEIGHT = 2.0
TRIGRAM_WEIGHT = 1.0

# Function words dilute the intent signal and inflate norms; dropping them
# measurably widens the related/unrelated margin (calibration in ADR-0004).
STOPWORDS = frozenset([
    'a', 'an', 'the', 'i', 'my', 'me', 'it', 'is', 'was', 'be', 'been', 'are',
    'am', 'you', 'your', 'for', 'of', 'to', 'in', 'on', 'at', 'with', 'and',
    'or', 'but', 'please', 'can', 'could', 'would', 'like', 'want', 'need',
    'do', 'does', 'did', 'get', 'this', 'that', 'he', 'she', 'they', 'we',
])


class Embedder(Protocol):
    def embed(self, text: str) -> list[float]: ...


class HashedNgramEmbedder:
    """Word + character-trigram features hashed into a fixed-dim vector.

    Deterministic across processes (crc32, not builtin hash), L2-normalized.
    A lexical proxy for intent similarity — precision-first thresholds in
    retrieval compensate for its lack of semantics.
    """

    def __init__(self, dim: int = 512) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for feature, weight in self._features(text):
            vec[zlib.crc32(feature.encode()) % self.dim] += weight
        return _normalize(vec)

    def _features(self, text: str) -> list[tuple[str, float]]:
        words = [w for w in re.findall(r'[a-z0-9#]+', text.lower()) if w not in STOPWORDS]
        feats = [(f'w:{w}', WORD_WEIGHT) for w in words]
        for word in words:
            padded = f'^{word}$'
            feats.extend(
                (f't:{padded[i:i + 3]}', TRIGRAM_WEIGHT) for i in range(len(padded) - 2)
            )
        return feats


def _normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return vec
    return [x / norm for x in vec]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))
