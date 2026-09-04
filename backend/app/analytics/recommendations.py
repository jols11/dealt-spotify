from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone

from app.analytics.sessions import PlayRecord
from app.analytics.transitions import Transition


@dataclass
class Recommendation:
    artist_id: int
    artist_name: str
    score: float
    reason: str
    last_played_days_ago: int | None
    historical_plays: int


def recommend_revisits(
    events: list[PlayRecord],
    transitions: list[Transition],
    now: datetime | None = None,
    limit: int = 6,
) -> list[Recommendation]:
    """Transparent heuristic ranking — not a trained model and not Spotify radio.

    score = 0.45 * historical_share
          + 0.35 * recency_gap_weight
          + 0.20 * neighbor_pull

    - historical_share: how much of all listening this artist occupied
    - recency_gap_weight: frequent artists that have gone quiet recently
    - neighbor_pull: artists often reached from currently active artists
    """
    if not events:
        return []

    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    by_artist: dict[int, list[PlayRecord]] = defaultdict(list)
    names: dict[int, str] = {}
    for event in events:
        played = event.played_at
        if played.tzinfo is None:
            played = played.replace(tzinfo=timezone.utc)
        by_artist[event.artist_id].append(event)
        names[event.artist_id] = event.artist_name

    total = len(events)
    last_play = {artist_id: max(item.played_at for item in plays) for artist_id, plays in by_artist.items()}
    for artist_id, stamp in list(last_play.items()):
        if stamp.tzinfo is None:
            last_play[artist_id] = stamp.replace(tzinfo=timezone.utc)

    recent_cutoff_days = 14
    recent_artists = {
        artist_id
        for artist_id, stamp in last_play.items()
        if (now - stamp).days <= recent_cutoff_days
    }

    outbound: dict[int, list[Transition]] = defaultdict(list)
    inbound: dict[int, list[Transition]] = defaultdict(list)
    for edge in transitions:
        outbound[edge.source_artist_id].append(edge)
        inbound[edge.target_artist_id].append(edge)

    scored: list[Recommendation] = []
    for artist_id, plays in by_artist.items():
        historical_share = len(plays) / total
        days_ago = (now - last_play[artist_id]).days
        recency_gap = min(days_ago / 45.0, 1.5) * historical_share
        neighbor_pull = 0.0
        reason_parts: list[str] = []

        related = inbound.get(artist_id, [])
        related.sort(key=lambda item: -item.count)
        for edge in related[:3]:
            if edge.source_artist_id in recent_artists and artist_id not in recent_artists:
                neighbor_pull += edge.probability * 0.5
                reason_parts.append(
                    f"You often move from {edge.source_artist_name} to {edge.target_artist_name} "
                    f"({edge.count} times), but {edge.target_artist_name} has been quiet."
                )

        if days_ago >= 14 and historical_share >= 0.03:
            reason_parts.append(
                f"Once a regular in your mix ({len(plays)} plays), last heard {days_ago} days ago."
            )
        elif historical_share >= 0.08:
            reason_parts.append(f"A durable part of your library, with {len(plays)} recorded plays.")

        score = 0.45 * historical_share + 0.35 * recency_gap + 0.20 * neighbor_pull
        if not reason_parts:
            continue
        scored.append(
            Recommendation(
                artist_id=artist_id,
                artist_name=names[artist_id],
                score=round(score, 5),
                reason=reason_parts[0],
                last_played_days_ago=days_ago,
                historical_plays=len(plays),
            )
        )

    scored.sort(key=lambda item: -item.score)
    # Prefer artists that actually receded, not the current #1.
    filtered = [item for item in scored if (item.last_played_days_ago or 0) >= 7]
    chosen = filtered or scored
    return chosen[:limit]
