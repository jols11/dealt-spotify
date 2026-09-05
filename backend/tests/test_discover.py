from app.services.discover import bridge_playlist, search_tracks, similar_tracks
from app.services.spotify_urls import parse_track_ref


def test_parse_open_spotify_url():
    kind, track_id = parse_track_ref("https://open.spotify.com/track/3n3Ppam7vgaVa1iaAAgDnh?si=abc")
    assert kind == "id"
    assert track_id == "3n3Ppam7vgaVa1iaAAgDnh"


def test_parse_uri_and_query():
    assert parse_track_ref("spotify:track:3n3Ppam7vgaVa1iaAAgDnh")[1] == "3n3Ppam7vgaVa1iaAAgDnh"
    kind, query = parse_track_ref("SZA Kill Bill")
    assert kind == "query"
    assert "Kill Bill" in query


def test_similar_and_bridge_use_local_catalog(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db.base import Base
    from app.models import entities  # noqa: F401
    from app.services.demo_seed import generate_demo_events
    from app.services.pipeline import rebuild_derived

    engine = create_engine(f"sqlite:///{tmp_path}/d.db")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    db = Session()
    user = generate_demo_events(db, days=40, seed=3)
    rebuild_derived(db, user)

    hits = search_tracks(db, user, "Kill Bill")
    assert any(item.name == "Kill Bill" for item in hits)

    similar = similar_tracks(db, user, "SZA Kill Bill")
    assert similar["seed"]["name"] == "Kill Bill"
    assert similar["items"]
    assert all(item["name"] != "Kill Bill" or item["artist_name"] != "SZA" for item in similar["items"])

    bridged = bridge_playlist(db, user, "Drake Passionfruit", "Phoebe Bridgers Kyoto", length=6, unit="songs")
    assert bridged["steps"][0]["role"] == "start"
    assert bridged["steps"][-1]["role"] == "end"
    assert bridged["steps"][0]["name"] == "Passionfruit"
    assert bridged["steps"][-1]["name"] == "Kyoto"
    assert bridged["song_count"] >= 3
    pop_rock = bridge_playlist(db, user, "Cruel Summer", "Karma Police", length=7, unit="songs")
    assert pop_rock["steps"][0]["name"] == "Cruel Summer"
    assert pop_rock["steps"][-1]["name"] == "Karma Police"
    assert [step["spotify_id"] for step in bridged["steps"]] != [step["spotify_id"] for step in pop_rock["steps"]]
    timed = bridge_playlist(db, user, "Drake Passionfruit", "Phoebe Bridgers Kyoto", length=12, unit="minutes")
    assert timed["duration_ms"] >= 12 * 60 * 1000 or timed["song_count"] >= 3
    db.close()
