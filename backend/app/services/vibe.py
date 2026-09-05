"""Genre-pace walk for Dealt.

Spotify Audio Features / Analysis (tempo/BPM, danceability, etc.) are not used.
Pace is inferred from artist genre tags so a deal can ramp from one vibe to another
as soon as Search + Get Artist work.
"""

from __future__ import annotations

import networkx as nx

# 0 quiet / slow-feeling tags → 1 high-energy tags. Not BPM from audio.
GENRE_PACE: dict[str, float] = {
    "acoustic": 0.22,
    "afrobeats": 0.7,
    "alt pop": 0.48,
    "alt r&b": 0.42,
    "alt rock": 0.58,
    "alternative": 0.5,
    "ambient": 0.12,
    "art pop": 0.4,
    "bedroom pop": 0.32,
    "classical": 0.18,
    "country": 0.38,
    "dance": 0.82,
    "dance pop": 0.78,
    "edm": 0.88,
    "electronic": 0.7,
    "emo": 0.52,
    "folk": 0.24,
    "funk": 0.62,
    "hip hop": 0.72,
    "house": 0.84,
    "indie": 0.4,
    "indie folk": 0.28,
    "indie pop": 0.46,
    "indie rock": 0.5,
    "jazz": 0.3,
    "k-pop": 0.76,
    "latin": 0.68,
    "metal": 0.86,
    "pop": 0.58,
    "pop rap": 0.7,
    "punk": 0.8,
    "r&b": 0.45,
    "rap": 0.74,
    "reggaeton": 0.78,
    "rock": 0.6,
    "singer-songwriter": 0.26,
    "soul": 0.4,
    "trap": 0.8,
}


def _norm(tag: str) -> str:
    return tag.strip().lower()


def pace_for_genres(genres: list[str]) -> float:
    scores = [GENRE_PACE[key] for key in (_norm(g) for g in genres) if key in GENRE_PACE]
    if scores:
        return sum(scores) / len(scores)
    # Unknown Spotify tags: prefer mid so we still interpolate.
    return 0.5


def _genre_graph() -> nx.Graph:
    graph = nx.Graph()
    for name, pace in GENRE_PACE.items():
        graph.add_node(name, pace=pace)
    links = [
        ("folk", "indie folk"),
        ("indie folk", "indie"),
        ("indie", "indie pop"),
        ("indie pop", "pop"),
        ("pop", "dance pop"),
        ("dance pop", "dance"),
        ("dance", "house"),
        ("house", "edm"),
        ("pop", "alt pop"),
        ("alt pop", "art pop"),
        ("pop", "k-pop"),
        ("r&b", "alt r&b"),
        ("r&b", "soul"),
        ("r&b", "pop"),
        ("r&b", "rap"),
        ("rap", "hip hop"),
        ("hip hop", "trap"),
        ("rap", "pop rap"),
        ("pop rap", "pop"),
        ("indie", "indie rock"),
        ("indie rock", "alt rock"),
        ("alt rock", "rock"),
        ("rock", "punk"),
        ("rock", "metal"),
        ("electronic", "house"),
        ("electronic", "funk"),
        ("afrobeats", "r&b"),
        ("latin", "reggaeton"),
        ("latin", "pop"),
        ("country", "folk"),
        ("jazz", "soul"),
        ("ambient", "classical"),
        ("ambient", "folk"),
        ("bedroom pop", "indie pop"),
        ("singer-songwriter", "folk"),
        ("emo", "indie rock"),
    ]
    for left, right in links:
        graph.add_edge(left, right)
    # Soft links by nearby pace so any two tags can still meet.
    names = list(GENRE_PACE)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            if abs(GENRE_PACE[left] - GENRE_PACE[right]) <= 0.08 and not graph.has_edge(left, right):
                graph.add_edge(left, right)
    return graph


def _best_tag(genres: list[str]) -> str | None:
    known = [_norm(g) for g in genres if _norm(g) in GENRE_PACE]
    if not known:
        return None
    return min(known, key=lambda tag: abs(GENRE_PACE[tag] - pace_for_genres(known)))


def genre_waypoints(start_genres: list[str], end_genres: list[str], steps: int) -> list[str]:
    """Return `steps` genre tags walking from the opening vibe toward the close."""
    if steps <= 0:
        return []
    graph = _genre_graph()
    start_tag = _best_tag(start_genres) or "pop"
    end_tag = _best_tag(end_genres) or "indie"
    if start_tag not in graph:
        start_tag = "pop"
    if end_tag not in graph:
        end_tag = "indie"
    try:
        path = nx.shortest_path(graph, start_tag, end_tag)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        path = [start_tag, end_tag]
    if len(path) == 1:
        path = [path[0], path[0]]
    # Sample along the path so a 7-card hand gets a smooth ramp, not one hop.
    waypoints: list[str] = []
    last_index = max(len(path) - 1, 1)
    for i in range(steps):
        t = (i + 1) / (steps + 1)
        index = min(int(round(t * last_index)), last_index)
        waypoints.append(path[index])
    return waypoints
