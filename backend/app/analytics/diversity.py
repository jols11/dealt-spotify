from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import log2

from app.analytics.sessions import PlayRecord
from app.analytics.transitions import Transition


@dataclass(frozen=True)
class DiversityMetrics:
    unique_artists: int
    unique_tracks: int
    event_count: int
    artist_entropy: float
    normalized_entropy: float
    herfindahl_index: float
    top_artist_share: float
    top_artist_name: str | None
    repeat_rate: float
    transition_diversity: float
    interpretation: str


def _entropy(counts: Counter[int]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        if count <= 0:
            continue
        probability = count / total
        entropy -= probability * log2(probability)
    return entropy


def compute_diversity(
    events: list[PlayRecord],
    transitions: list[Transition] | None = None,
) -> DiversityMetrics:
    """Behavioral concentration metrics derived from play frequencies.

    Artist entropy H = -Σ p_i log2(p_i) measures how evenly listening is
    spread across artists. Normalized entropy divides by log2(n) so 1.0 is
    perfectly even and 0.0 is a single artist. The Herfindahl index is
    Σ p_i² (higher means more concentrated). Repeat rate is 1 - unique_tracks
    / events. These describe listening mix, not personality.
    """
    if not events:
        return DiversityMetrics(
            unique_artists=0,
            unique_tracks=0,
            event_count=0,
            artist_entropy=0.0,
            normalized_entropy=0.0,
            herfindahl_index=0.0,
            top_artist_share=0.0,
            top_artist_name=None,
            repeat_rate=0.0,
            transition_diversity=0.0,
            interpretation="There is not enough listening history to describe diversity yet.",
        )

    artist_counts: Counter[int] = Counter(event.artist_id for event in events)
    names = {event.artist_id: event.artist_name for event in events}
    entropy = _entropy(artist_counts)
    n_artists = len(artist_counts)
    max_entropy = log2(n_artists) if n_artists > 1 else 1.0
    normalized = entropy / max_entropy if max_entropy else 0.0
    total = len(events)
    shares = [count / total for count in artist_counts.values()]
    hhi = sum(share * share for share in shares)
    top_id, top_count = artist_counts.most_common(1)[0]
    unique_tracks = len({event.track_id for event in events})
    repeat_rate = 1.0 - (unique_tracks / total)

    transition_diversity = 0.0
    if transitions:
        sources = {item.source_artist_id for item in transitions}
        if sources:
            transition_diversity = len(transitions) / len(sources)

    if normalized >= 0.78 and top_count / total < 0.18:
        interpretation = "Your listening is relatively spread out — no single artist dominates the mix."
    elif top_count / total >= 0.35:
        interpretation = f"{names[top_id]} occupies a large share of your recent listening."
    else:
        interpretation = "You have a recognizable core of artists, with a wider ring of occasional plays."

    return DiversityMetrics(
        unique_artists=n_artists,
        unique_tracks=unique_tracks,
        event_count=total,
        artist_entropy=round(entropy, 4),
        normalized_entropy=round(normalized, 4),
        herfindahl_index=round(hhi, 4),
        top_artist_share=round(top_count / total, 4),
        top_artist_name=names[top_id],
        repeat_rate=round(repeat_rate, 4),
        transition_diversity=round(transition_diversity, 4),
        interpretation=interpretation,
    )
