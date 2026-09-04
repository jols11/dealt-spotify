from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from app.analytics.sessions import SessionRecord


@dataclass(frozen=True)
class Transition:
    source_artist_id: int
    source_artist_name: str
    target_artist_id: int
    target_artist_name: str
    count: int
    probability: float


def transitions_from_sessions(sessions: list[SessionRecord]) -> list[Transition]:
    """Count directed artist handoffs inside a session.

    Self-transitions (the same artist twice in a row) are kept because repeat
    listening is a real behavioral signal, but the UI can filter them out.
    """
    counts: dict[tuple[int, int], int] = defaultdict(int)
    names: dict[int, str] = {}

    for session in sessions:
        events = session.events
        for left, right in zip(events, events[1:]):
            counts[(left.artist_id, right.artist_id)] += 1
            names[left.artist_id] = left.artist_name
            names[right.artist_id] = right.artist_name

    outbound: dict[int, int] = defaultdict(int)
    for (source, _target), count in counts.items():
        outbound[source] += count

    result: list[Transition] = []
    for (source, target), count in counts.items():
        denominator = outbound[source]
        probability = count / denominator if denominator else 0.0
        result.append(
            Transition(
                source_artist_id=source,
                source_artist_name=names.get(source, "Unknown"),
                target_artist_id=target,
                target_artist_name=names.get(target, "Unknown"),
                count=count,
                probability=probability,
            )
        )
    return sorted(result, key=lambda item: (-item.count, -item.probability, item.source_artist_name))
