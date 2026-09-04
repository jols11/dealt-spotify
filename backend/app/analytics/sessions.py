from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable


@dataclass(frozen=True)
class PlayRecord:
    event_id: int | None
    track_id: int
    artist_id: int
    artist_name: str
    track_name: str
    played_at: datetime
    genre: str | None = None
    album_name: str | None = None
    album_image_url: str | None = None
    duration_ms: int | None = None


@dataclass
class SessionRecord:
    start_time: datetime
    end_time: datetime
    events: list[PlayRecord] = field(default_factory=list)

    @property
    def track_count(self) -> int:
        return len(self.events)

    @property
    def unique_artist_count(self) -> int:
        return len({event.artist_id for event in self.events})

    @property
    def dominant_artist_id(self) -> int | None:
        if not self.events:
            return None
        counts = Counter(event.artist_id for event in self.events)
        return counts.most_common(1)[0][0]

    @property
    def dominant_artist_name(self) -> str | None:
        artist_id = self.dominant_artist_id
        if artist_id is None:
            return None
        for event in self.events:
            if event.artist_id == artist_id:
                return event.artist_name
        return None

    @property
    def dominant_genre(self) -> str | None:
        genres = [event.genre for event in self.events if event.genre]
        if not genres:
            return None
        return Counter(genres).most_common(1)[0][0]

    @property
    def duration_seconds(self) -> int:
        if not self.events:
            return 0
        return int((self.end_time - self.start_time).total_seconds())


def sessionize(
    events: Iterable[PlayRecord],
    gap_minutes: int = 30,
) -> list[SessionRecord]:
    """Group chronological plays into sessions using an inactivity gap.

    A new session starts when the time between consecutive plays is strictly
    greater than `gap_minutes`. A gap equal to the threshold stays in-session.
    """
    ordered = sorted(events, key=lambda item: item.played_at)
    if not ordered:
        return []

    gap = timedelta(minutes=gap_minutes)
    sessions: list[SessionRecord] = []
    current: list[PlayRecord] = [ordered[0]]

    for previous, current_event in zip(ordered, ordered[1:]):
        delta = current_event.played_at - previous.played_at
        if delta > gap:
            sessions.append(
                SessionRecord(
                    start_time=current[0].played_at,
                    end_time=current[-1].played_at,
                    events=current,
                )
            )
            current = [current_event]
        else:
            current.append(current_event)

    sessions.append(
        SessionRecord(
            start_time=current[0].played_at,
            end_time=current[-1].played_at,
            events=current,
        )
    )
    return sessions
