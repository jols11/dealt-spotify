from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha1

import numpy as np
from sqlalchemy.orm import Session

from app.models.entities import Artist, ArtistGenre, Genre, ListeningEvent, Track, TrackArtist, User

DEMO_SPOTIFY_ID = "demo-synthetic-listener"

# Public artist names used as labels in a synthetic timeline. Plays are invented.
CATALOG: list[dict] = [
    {"name": "Drake", "genres": ["rap", "r&b"], "tracks": ["Passionfruit", "Marvins Room", "Fair Trade", "Headlines"]},
    {"name": "SZA", "genres": ["r&b"], "tracks": ["Snooze", "Kill Bill", "Good Days", "Shirt"]},
    {"name": "Kendrick Lamar", "genres": ["rap"], "tracks": ["HUMBLE.", "LOVE.", "N95", "tv off"]},
    {"name": "J. Cole", "genres": ["rap"], "tracks": ["No Role Modelz", "Love Yourz", "Middle Child"]},
    {"name": "Frank Ocean", "genres": ["r&b", "alt r&b"], "tracks": ["Pink + White", "Ivy", "Nights", "Self Control"]},
    {"name": "The Weeknd", "genres": ["r&b", "pop"], "tracks": ["Blinding Lights", "Die For You", "Call Out My Name"]},
    {"name": "Taylor Swift", "genres": ["pop"], "tracks": ["cardigan", "maroon", "Cruel Summer", "Tolerate It"]},
    {"name": "Phoebe Bridgers", "genres": ["indie", "folk"], "tracks": ["Motion Sickness", "Kyoto", "Scott Street"]},
    {"name": "Mitski", "genres": ["indie"], "tracks": ["Nobody", "First Love / Late Spring", "My Love Mine All Mine"]},
    {"name": "Bon Iver", "genres": ["indie", "folk"], "tracks": ["Holocene", "Hey, Ma", "8 (circle)"]},
    {"name": "Radiohead", "genres": ["alt rock"], "tracks": ["Weird Fishes", "Karma Police", "Daydreaming"]},
    {"name": "Fred again..", "genres": ["electronic", "house"], "tracks": ["adore u", "leavemealone", "Rumble"]},
    {"name": "Four Tet", "genres": ["electronic"], "tracks": ["Baby", "Lush", "Dreamer"]},
    {"name": "Kaytranada", "genres": ["electronic", "r&b"], "tracks": ["LITE SPOTS", "YOU'RE THE ONE", "Intimidated"]},
    {"name": "Bad Bunny", "genres": ["latin", "reggaeton"], "tracks": ["Tití Me Preguntó", "Moscow Mule", "DtMF"]},
    {"name": "ROSALÍA", "genres": ["latin", "pop"], "tracks": ["MALAMENTE", "SAOKO", "Despechá"]},
    {"name": "Burna Boy", "genres": ["afrobeats"], "tracks": ["Last Last", "On The Low", "Ye"]},
    {"name": "Tems", "genres": ["afrobeats", "r&b"], "tracks": ["Free Mind", "Higher", "Me & U"]},
    {"name": "Clairo", "genres": ["indie", "pop"], "tracks": ["Bags", "Sofia", "Pretty Girl"]},
    {"name": "Japanese Breakfast", "genres": ["indie"], "tracks": ["Be Sweet", "Posing in Bondage", "Paprika"]},
    {"name": "The National", "genres": ["indie", "alt rock"], "tracks": ["I Need My Girl", "Bloodbuzz Ohio", "The System Only Dreams in Total Darkness"]},
    {"name": "Khruangbin", "genres": ["funk", "psychedelic"], "tracks": ["Time (You and I)", "Maria También", "People Everywhere"]},
    {"name": "Norah Jones", "genres": ["jazz", "pop"], "tracks": ["Don't Know Why", "Come Away With Me", "Sunrise"]},
    {"name": "Lorde", "genres": ["pop", "alt pop"], "tracks": ["Ribs", "Green Light", "Solar Power"]},
    {"name": "Billie Eilish", "genres": ["pop", "alt pop"], "tracks": ["ocean eyes", "Happier Than Ever", "WILDFLOWER"]},
    {"name": "Olivia Rodrigo", "genres": ["pop"], "tracks": ["drivers license", "traitor", "vampire"]},
    {"name": "Harry Styles", "genres": ["pop"], "tracks": ["Adore You", "Cherry", "Sign of the Times"]},
    {"name": "Kacey Musgraves", "genres": ["country", "pop"], "tracks": ["Slow Burn", "Golden Hour", "Rainbow"]},
    {"name": "Tyler, The Creator", "genres": ["rap"], "tracks": ["EARFQUAKE", "See You Again", "NEW MAGIC WAND"]},
    {"name": "Bryson Tiller", "genres": ["r&b"], "tracks": ["Don't", "Exchange", "Right My Wrongs"]},
]


def _synthetic_id(label: str) -> str:
    return "syn-" + sha1(label.encode("utf-8")).hexdigest()[:16]


def get_or_create_demo_user(db: Session) -> User:
    user = db.query(User).filter(User.spotify_account_id == DEMO_SPOTIFY_ID).one_or_none()
    if user is None:
        user = User(
            spotify_account_id=DEMO_SPOTIFY_ID,
            display_name="Avery Chen",
            country="US",
            product="premium",
            is_demo=True,
        )
        db.add(user)
        db.flush()
    else:
        user.is_demo = True
        user.display_name = user.display_name or "Avery Chen"
    return user


def _ensure_catalog(db: Session) -> dict[str, tuple[Artist, list[Track]]]:
    catalog: dict[str, tuple[Artist, list[Track]]] = {}
    for entry in CATALOG:
        artist = db.query(Artist).filter(Artist.spotify_id == _synthetic_id(entry["name"])).one_or_none()
        if artist is None:
            artist = Artist(spotify_id=_synthetic_id(entry["name"]), name=entry["name"], popularity=70)
            db.add(artist)
            db.flush()
        for genre_name in entry["genres"]:
            genre = db.query(Genre).filter(Genre.name == genre_name).one_or_none()
            if genre is None:
                genre = Genre(name=genre_name)
                db.add(genre)
                db.flush()
            exists = (
                db.query(ArtistGenre)
                .filter(ArtistGenre.artist_id == artist.id, ArtistGenre.genre_id == genre.id)
                .one_or_none()
            )
            if exists is None:
                db.add(ArtistGenre(artist_id=artist.id, genre_id=genre.id))
        tracks: list[Track] = []
        for title in entry["tracks"]:
            spotify_id = _synthetic_id(f"{entry['name']}:{title}")
            track = db.query(Track).filter(Track.spotify_id == spotify_id).one_or_none()
            if track is None:
                track = Track(
                    spotify_id=spotify_id,
                    name=title,
                    album_name=f"{entry['name']} — Selected",
                    duration_ms=int(180000 + (len(title) * 137) % 120000),
                    primary_artist_id=artist.id,
                )
                db.add(track)
                db.flush()
                db.add(TrackArtist(track_id=track.id, artist_id=artist.id, position=0))
            tracks.append(track)
        catalog[entry["name"]] = (artist, tracks)
    db.flush()
    return catalog


def _pick_artist(rng: np.random.Generator, hour: int, weekday: int, month: int) -> str:
    night = ["SZA", "Frank Ocean", "The Weeknd", "Bryson Tiller", "Drake"]
    morning = ["Phoebe Bridgers", "Mitski", "Bon Iver", "Clairo", "Norah Jones"]
    commute = ["Kendrick Lamar", "J. Cole", "Drake", "Tyler, The Creator", "Kaytranada"]
    evening = ["Taylor Swift", "Lorde", "Billie Eilish", "Olivia Rodrigo", "Harry Styles"]
    weekend = ["Fred again..", "Four Tet", "Kaytranada", "Khruangbin"]
    summer = ["Bad Bunny", "ROSALÍA", "Burna Boy", "Tems"]
    winter = ["Bon Iver", "Radiohead", "The National", "Phoebe Bridgers"]

    if month in {6, 7, 8} and rng.random() < 0.22:
        return rng.choice(summer)
    if month in {12, 1, 2} and rng.random() < 0.22:
        return rng.choice(winter)
    if weekday >= 5 and rng.random() < 0.45:
        return rng.choice(weekend)
    if hour >= 21 or hour < 5:
        return rng.choice(night)
    if 5 <= hour < 11:
        return rng.choice(morning)
    if 11 <= hour < 17:
        return rng.choice(commute)
    return rng.choice(evening)


# Sticky transitions: once an artist is playing, the next artist is often related.
FOLLOW = {
    "Drake": ["SZA", "Bryson Tiller", "J. Cole", "Kendrick Lamar"],
    "SZA": ["Frank Ocean", "Drake", "Tems", "The Weeknd"],
    "Frank Ocean": ["SZA", "Tyler, The Creator", "Bon Iver"],
    "Fred again..": ["Four Tet", "Kaytranada", "Fred again.."],
    "Four Tet": ["Fred again..", "Kaytranada", "Khruangbin"],
    "Taylor Swift": ["Phoebe Bridgers", "Lorde", "Olivia Rodrigo"],
    "Phoebe Bridgers": ["Mitski", "Bon Iver", "Taylor Swift"],
    "Kendrick Lamar": ["J. Cole", "Tyler, The Creator", "Drake"],
}


def generate_demo_events(db: Session, days: int = 180, seed: int = 42) -> User:
    user = get_or_create_demo_user(db)
    catalog = _ensure_catalog(db)

    existing = db.query(ListeningEvent).filter(ListeningEvent.user_id == user.id).count()
    if existing > 200:
        return user

    rng = np.random.default_rng(seed)
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(days=days)
    cursor = start + timedelta(hours=int(rng.integers(8, 20)))
    last_artist: str | None = None
    pending: list[ListeningEvent] = []
    seen: set[tuple[int, datetime]] = set()

    while cursor < now:
        if rng.random() < 0.18:
            cursor += timedelta(hours=int(rng.integers(8, 30)))
            last_artist = None
            continue

        session_length = int(rng.integers(4, 14))
        hour = cursor.hour
        weekday = cursor.weekday()
        month = cursor.month
        for index in range(session_length):
            if last_artist and last_artist in FOLLOW and rng.random() < 0.62:
                artist_name = str(rng.choice(FOLLOW[last_artist]))
            else:
                artist_name = str(_pick_artist(rng, hour, weekday, month))
            _artist, tracks = catalog[artist_name]
            track = tracks[int(rng.integers(0, len(tracks)))]
            played_at = cursor + timedelta(seconds=int(index * rng.integers(180, 280)))
            if played_at >= now:
                break
            key = (track.id, played_at)
            if key in seen:
                continue
            seen.add(key)
            pending.append(
                ListeningEvent(
                    user_id=user.id,
                    track_id=track.id,
                    played_at=played_at,
                    context_type="synthetic",
                    context_uri=None,
                )
            )
            last_artist = artist_name
        if rng.random() < 0.25:
            cursor += timedelta(minutes=int(rng.integers(35, 90)))
        else:
            cursor += timedelta(hours=float(rng.uniform(3.0, 18.0)))
            last_artist = None

    db.add_all(pending)
    db.commit()
    return user


def synthetic_personas(db: Session) -> dict[str, list]:
    """Lightweight alternate histories for the similarity demo (same catalog)."""
    from app.analytics.sessions import PlayRecord

    catalog = _ensure_catalog(db)
    rng = np.random.default_rng(99)
    now = datetime.now(timezone.utc)

    def make(weights: dict[str, float], n: int = 80) -> list[PlayRecord]:
        names = list(weights)
        probs = np.array([weights[name] for name in names], dtype=float)
        probs = probs / probs.sum()
        records: list[PlayRecord] = []
        for i in range(n):
            name = str(rng.choice(names, p=probs))
            artist, tracks = catalog[name]
            track = tracks[i % len(tracks)]
            records.append(
                PlayRecord(
                    event_id=None,
                    track_id=track.id,
                    artist_id=artist.id,
                    artist_name=artist.name,
                    track_name=track.name,
                    played_at=now - timedelta(hours=i),
                    genre=None,
                )
            )
        return records

    return {
        "Night Owl R&B": make({"SZA": 0.3, "Frank Ocean": 0.25, "The Weeknd": 0.2, "Drake": 0.15, "Tems": 0.1}),
        "Weekend Electronic": make({"Fred again..": 0.35, "Four Tet": 0.3, "Kaytranada": 0.2, "Khruangbin": 0.15}),
        "Pop Forward": make({"Taylor Swift": 0.3, "Olivia Rodrigo": 0.2, "Lorde": 0.2, "Billie Eilish": 0.2, "Harry Styles": 0.1}),
    }
