from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from app.analytics.sessions import PlayRecord
from app.analytics.temporal import hour_bucket


@dataclass
class ArtistCluster:
    cluster_id: int
    label: str
    size: int
    artists: list[dict]
    interpretation: str


def _feature_matrix(events: list[PlayRecord]) -> tuple[list[int], list[str], list[list[float]]]:
    """Build behavioral vectors per artist from the listener's own plays.

    Features are derived statistics (share, hour-of-day mix, weekend share,
    monthly mix), not Spotify audio content. This avoids training on
    restricted audio features.
    """
    by_artist: dict[int, list[PlayRecord]] = defaultdict(list)
    names: dict[int, str] = {}
    for event in events:
        by_artist[event.artist_id].append(event)
        names[event.artist_id] = event.artist_name

    total = max(len(events), 1)
    artist_ids = sorted(by_artist, key=lambda artist_id: -len(by_artist[artist_id]))
    rows: list[list[float]] = []
    for artist_id in artist_ids:
        plays = by_artist[artist_id]
        n = len(plays)
        share = n / total
        buckets = {"Late night": 0.0, "Morning": 0.0, "Afternoon": 0.0, "Evening": 0.0, "Night": 0.0}
        weekend = 0.0
        months = [0.0] * 12
        for play in plays:
            buckets[hour_bucket(play.played_at.hour)] += 1
            if play.played_at.weekday() >= 5:
                weekend += 1
            months[play.played_at.month - 1] += 1
        row = [
            share,
            weekend / n,
            buckets["Late night"] / n,
            buckets["Morning"] / n,
            buckets["Afternoon"] / n,
            buckets["Evening"] / n,
            buckets["Night"] / n,
            *[count / n for count in months],
        ]
        rows.append(row)
    return artist_ids, [names[artist_id] for artist_id in artist_ids], rows


def _choose_k(n_artists: int) -> int:
    if n_artists < 4:
        return 1
    if n_artists < 8:
        return 2
    if n_artists < 16:
        return 3
    return 4


def _playful_label(cluster_plays: list[PlayRecord], fallback: int) -> tuple[str, str]:
    if not cluster_plays:
        return f"Cluster {fallback + 1}", "Too little activity to interpret this group."
    hours = Counter(hour_bucket(play.played_at.hour) for play in cluster_plays)
    genres = Counter(play.genre for play in cluster_plays if play.genre)
    peak_hour = hours.most_common(1)[0][0]
    genre = genres.most_common(1)[0][0] if genres else "mixed artists"
    labels = {
        "Late night": "After-hours core",
        "Night": "Night listening set",
        "Morning": "Morning rotation",
        "Afternoon": "Daytime thread",
        "Evening": "Evening companions",
    }
    title = f"{labels.get(peak_hour, 'Listening set')} · {genre}"
    interpretation = (
        f"A playful grouping, not a scientific genre: these artists tend to show up in "
        f"{peak_hour.lower()} listening, often near {genre}."
    )
    return title, interpretation


def cluster_artists(events: list[PlayRecord], max_artists: int = 24) -> list[ArtistCluster]:
    if len({event.artist_id for event in events}) < 3:
        return []

    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    import numpy as np

    artist_ids, names, rows = _feature_matrix(events)
    artist_ids = artist_ids[:max_artists]
    names = names[:max_artists]
    rows = rows[:max_artists]
    matrix = np.array(rows, dtype=float)
    scaled = StandardScaler().fit_transform(matrix)
    k = _choose_k(len(artist_ids))
    if k <= 1:
        return []

    model = KMeans(n_clusters=k, n_init=10, random_state=7)
    labels = model.fit_predict(scaled)

    grouped: dict[int, list[int]] = defaultdict(list)
    for index, cluster_id in enumerate(labels):
        grouped[int(cluster_id)].append(index)

    result: list[ArtistCluster] = []
    for cluster_id, indices in grouped.items():
        cluster_artist_ids = {artist_ids[i] for i in indices}
        cluster_plays = [event for event in events if event.artist_id in cluster_artist_ids]
        title, interpretation = _playful_label(cluster_plays, cluster_id)
        artists = []
        for i in indices:
            play_count = sum(1 for event in events if event.artist_id == artist_ids[i])
            artists.append({"id": artist_ids[i], "name": names[i], "plays": play_count})
        artists.sort(key=lambda item: -item["plays"])
        result.append(
            ArtistCluster(
                cluster_id=cluster_id,
                label=title,
                size=len(artists),
                artists=artists[:8],
                interpretation=interpretation,
            )
        )
    return sorted(result, key=lambda item: -item.size)
