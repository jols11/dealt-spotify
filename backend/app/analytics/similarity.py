from __future__ import annotations

from collections import Counter

import numpy as np

from app.analytics.sessions import PlayRecord


def artist_share_vector(events: list[PlayRecord], vocabulary: list[int]) -> np.ndarray:
    counts = Counter(event.artist_id for event in events)
    total = max(sum(counts.values()), 1)
    return np.array([counts.get(artist_id, 0) / total for artist_id in vocabulary], dtype=float)


def cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    denom = float(np.linalg.norm(left) * np.linalg.norm(right))
    if denom == 0:
        return 0.0
    return float(np.dot(left, right) / denom)


def compare_users(
    primary: list[PlayRecord],
    others: dict[str, list[PlayRecord]],
) -> list[dict]:
    """Compare artist-share vectors. This is pattern similarity, not people similarity."""
    vocabulary = sorted({event.artist_id for event in primary} | {event.artist_id for bucket in others.values() for event in bucket})
    if not vocabulary:
        return []
    primary_vec = artist_share_vector(primary, vocabulary)
    results = []
    for name, events in others.items():
        score = cosine_similarity(primary_vec, artist_share_vector(events, vocabulary))
        results.append(
            {
                "persona": name,
                "cosine_similarity": round(score, 4),
                "caveat": "Similar listening patterns, not similar people.",
            }
        )
    results.sort(key=lambda item: -item["cosine_similarity"])
    return results
