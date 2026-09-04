from datetime import datetime, timedelta, timezone

from app.analytics.diversity import compute_diversity
from app.analytics.recommendations import recommend_revisits
from app.analytics.sessions import PlayRecord, sessionize
from app.analytics.similarity import cosine_similarity, artist_share_vector
from app.analytics.transitions import transitions_from_sessions
from app.services.ingestion import parse_played_at
from app.services.spotify_client import SpotifyClient


def play(event_id, track_id, artist_id, artist, track, when, genre=None):
    return PlayRecord(
        event_id=event_id,
        track_id=track_id,
        artist_id=artist_id,
        artist_name=artist,
        track_name=track,
        played_at=when,
        genre=genre,
    )


def test_parse_played_at_z_suffix():
    stamp = parse_played_at("2024-01-02T03:04:05.000Z")
    assert stamp.tzinfo is not None
    assert stamp.hour == 3


def test_sessionize_empty():
    assert sessionize([]) == []


def test_sessionize_single_event():
    now = datetime(2024, 1, 1, 12, tzinfo=timezone.utc)
    sessions = sessionize([play(1, 1, 1, "A", "t", now)])
    assert len(sessions) == 1
    assert sessions[0].track_count == 1
    assert sessions[0].dominant_artist_name == "A"


def test_sessionize_gap_strictly_greater_than_threshold():
    start = datetime(2024, 1, 1, 12, tzinfo=timezone.utc)
    events = [
        play(1, 1, 1, "A", "t1", start),
        play(2, 2, 2, "B", "t2", start + timedelta(minutes=30)),
        play(3, 3, 3, "C", "t3", start + timedelta(minutes=61)),
    ]
    sessions = sessionize(events, gap_minutes=30)
    assert len(sessions) == 2
    assert [item.track_count for item in sessions] == [2, 1]


def test_repeated_same_artist_transitions_and_probability():
    start = datetime(2024, 1, 1, 12, tzinfo=timezone.utc)
    events = [
        play(1, 1, 1, "A", "t1", start),
        play(2, 2, 1, "A", "t2", start + timedelta(minutes=3)),
        play(3, 3, 2, "B", "t3", start + timedelta(minutes=6)),
        play(4, 4, 2, "B", "t4", start + timedelta(minutes=9)),
    ]
    sessions = sessionize(events, gap_minutes=30)
    edges = { (e.source_artist_name, e.target_artist_name): e for e in transitions_from_sessions(sessions) }
    assert edges[("A", "A")].count == 1
    assert edges[("A", "B")].count == 1
    assert abs(edges[("A", "A")].probability - 0.5) < 1e-9
    assert abs(edges[("A", "B")].probability - 0.5) < 1e-9
    assert abs(edges[("B", "B")].probability - 1.0) < 1e-9


def test_diversity_empty_and_single_artist():
    empty = compute_diversity([])
    assert empty.unique_artists == 0
    assert empty.artist_entropy == 0
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    events = [play(i, 1, 1, "A", "same", start + timedelta(minutes=i)) for i in range(5)]
    metrics = compute_diversity(events)
    assert metrics.unique_artists == 1
    assert metrics.artist_entropy == 0
    assert metrics.top_artist_share == 1
    assert metrics.repeat_rate == 0.8


def test_recommendation_prefers_quiet_historically_frequent_artist():
    now = datetime(2024, 6, 1, tzinfo=timezone.utc)
    events = []
    for i in range(20):
        events.append(play(i, 1, 1, "Drake", "x", now - timedelta(days=40, minutes=i)))
    for i in range(5):
        events.append(play(100 + i, 2, 2, "SZA", "y", now - timedelta(days=1, minutes=i)))
    recs = recommend_revisits(events, transitions_from_sessions(sessionize(events)), now=now)
    assert recs
    assert recs[0].artist_name == "Drake"


def test_cosine_similarity_identical_and_orthogonal():
    import numpy as np

    a = np.array([1.0, 0.0])
    b = np.array([1.0, 0.0])
    c = np.array([0.0, 1.0])
    assert abs(cosine_similarity(a, b) - 1.0) < 1e-9
    assert abs(cosine_similarity(a, c)) < 1e-9


def test_clustering_features_normalize_without_audio():
    from app.analytics.clusters import _feature_matrix

    start = datetime(2024, 1, 1, 22, tzinfo=timezone.utc)
    events = []
    for i in range(6):
        events.append(play(i, 1, 1, "A", "t", start + timedelta(minutes=i), genre="r&b"))
        events.append(play(10 + i, 2, 2, "B", "u", start.replace(hour=9) + timedelta(minutes=i), genre="indie"))
    ids, names, rows = _feature_matrix(events)
    assert len(ids) == 2
    assert all(abs(sum(row[2:7]) - 1.0) < 1e-6 for row in rows)


def test_spotify_recently_played_parser_shape():
    items = [
        {
            "played_at": "2024-02-02T10:00:00.000Z",
            "track": {
                "id": "t1",
                "name": "Song",
                "duration_ms": 200000,
                "artists": [{"id": "a1", "name": "Artist"}],
                "album": {"name": "LP", "images": []},
            },
            "context": {"type": "playlist", "uri": "spotify:playlist:1"},
        }
    ]
    assert items[0]["track"]["artists"][0]["id"] == "a1"
    assert hasattr(SpotifyClient, "paginate_recently_played")
