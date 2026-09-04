from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime

from app.analytics.sessions import PlayRecord
from app.analytics.transitions import Transition


def rising_artists(events: list[PlayRecord], limit: int = 4) -> list[dict]:
    if len(events) < 8:
        return []
    ordered = sorted(events, key=lambda item: item.played_at)
    midpoint = ordered[len(ordered) // 2].played_at
    first = [event for event in ordered if event.played_at < midpoint]
    second = [event for event in ordered if event.played_at >= midpoint]
    if not first or not second:
        return []
    first_counts = Counter(event.artist_id for event in first)
    second_counts = Counter(event.artist_id for event in second)
    names = {event.artist_id: event.artist_name for event in events}
    first_total = len(first)
    second_total = len(second)
    lifted = []
    for artist_id, later in second_counts.items():
        earlier_share = first_counts.get(artist_id, 0) / first_total
        later_share = later / second_total
        delta = later_share - earlier_share
        if delta > 0.02 and later >= 4:
            lifted.append(
                {
                    "artist_id": artist_id,
                    "name": names[artist_id],
                    "delta": round(delta, 4),
                    "insight": (
                        f"{names[artist_id]} has become more central to your listening "
                        "in the more recent half of this history."
                    ),
                }
            )
    lifted.sort(key=lambda item: -item["delta"])
    return lifted[:limit]


def overview_insights(
    events: list[PlayRecord],
    transitions: list[Transition],
    display_name: str,
) -> dict:
    if not events:
        return {
            "greeting": f"Hello, {display_name}",
            "headline": "Connect Spotify or open the demo to decode a listening history.",
            "period_label": None,
        }
    start = min(event.played_at for event in events)
    end = max(event.played_at for event in events)
    strongest = transitions[0] if transitions else None
    top = Counter(event.artist_id for event in events).most_common(1)[0]
    names = {event.artist_id: event.artist_name for event in events}
    return {
        "greeting": _greeting(end, display_name),
        "headline": "Your listening, decoded.",
        "period_label": f"{start.strftime('%b %Y')} – {end.strftime('%b %Y')}",
        "top_artist_insight": f"{names[top[0]]} is the artist you return to most in this window.",
        "strongest_transition_insight": (
            f"You most often move from {strongest.source_artist_name} to {strongest.target_artist_name} "
            "during the same listening session."
            if strongest and strongest.source_artist_id != strongest.target_artist_id
            else None
        ),
        "rising": rising_artists(events),
    }


def _greeting(when: datetime, name: str) -> str:
    hour = when.hour
    if hour < 5 or hour >= 21:
        prefix = "Good evening"
    elif hour < 12:
        prefix = "Good morning"
    elif hour < 17:
        prefix = "Good afternoon"
    else:
        prefix = "Good evening"
    return f"{prefix}, {name}"
