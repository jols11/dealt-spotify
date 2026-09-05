from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
from sqlalchemy.orm import Session

from app.models.entities import ArtistTransition, TrackFeedback, User
from app.services.auth import catalog_client_for_user
from app.services.demo_seed import CATALOG, FOLLOW
from app.services.spotify_client import SpotifyAPIError, SpotifyClient
from app.services.spotify_urls import parse_track_ref
from app.services.vibe import genre_waypoints, pace_for_genres


@dataclass
class ResolvedTrack:
    spotify_id: str
    name: str
    artist_name: str
    artist_spotify_id: str | None
    genres: list[str]
    album_name: str | None
    image_url: str | None
    url: str
    source: str  # spotify | catalog
    duration_ms: int = 210000


@dataclass
class ScoredTrack:
    track: ResolvedTrack
    reason: str
    score: float


def _open_url(spotify_id: str) -> str:
    if spotify_id.startswith("syn-"):
        return f"https://open.spotify.com/search/{spotify_id}"
    return f"https://open.spotify.com/track/{spotify_id}"


def _from_spotify_payload(track: dict, genres: list[str] | None = None) -> ResolvedTrack:
    artists = track.get("artists") or [{}]
    primary = artists[0] if artists else {}
    album = track.get("album") or {}
    images = album.get("images") or []
    spotify_id = track["id"]
    return ResolvedTrack(
        spotify_id=spotify_id,
        name=track.get("name") or "Unknown track",
        artist_name=primary.get("name") or "Unknown artist",
        artist_spotify_id=primary.get("id"),
        genres=genres or [],
        album_name=album.get("name"),
        image_url=images[0]["url"] if images else None,
        url=_open_url(spotify_id),
        source="spotify",
        duration_ms=int(track.get("duration_ms") or 210000),
    )


def _hydrate_genres(client: SpotifyClient, artist_id: str | None) -> list[str]:
    if not artist_id:
        return []
    try:
        artist = client.get_artist(artist_id)
    except SpotifyAPIError:
        return []
    return list(artist.get("genres") or [])


def _taste(db: Session, user: User) -> tuple[set[str], set[str], set[str]]:
    blocked_ids: set[str] = set()
    blocked_artists: set[str] = set()
    liked_artists: set[str] = set()
    for row in db.query(TrackFeedback).filter(TrackFeedback.user_id == user.id).all():
        if row.vote < 0:
            blocked_ids.add(row.spotify_id)
            if row.artist_name:
                blocked_artists.add(row.artist_name.lower())
        elif row.vote > 0 and row.artist_name:
            liked_artists.add(row.artist_name.lower())
    return blocked_ids, blocked_artists, liked_artists


def _prefer(options: list[ResolvedTrack], blocked_ids: set[str], blocked_artists: set[str], liked_artists: set[str]) -> list[ResolvedTrack]:
    kept: list[ResolvedTrack] = []
    for track in options:
        if track.spotify_id in blocked_ids:
            continue
        if track.artist_name.lower() in blocked_artists:
            continue
        kept.append(track)
    kept.sort(key=lambda track: 0 if track.artist_name.lower() in liked_artists else 1)
    return kept


def catalog_tracks() -> list[ResolvedTrack]:
    results: list[ResolvedTrack] = []
    for entry in CATALOG:
        for title in entry["tracks"]:
            from hashlib import sha1

            spotify_id = "syn-" + sha1(f"{entry['name']}:{title}".encode()).hexdigest()[:16]
            results.append(
                ResolvedTrack(
                    spotify_id=spotify_id,
                    name=title,
                    artist_name=entry["name"],
                    artist_spotify_id="syn-" + sha1(entry["name"].encode()).hexdigest()[:16],
                    genres=list(entry["genres"]),
                    album_name=f"{entry['name']} — Selected",
                    image_url=None,
                    url=f"https://open.spotify.com/search/{title} {entry['name']}".replace(" ", "%20"),
                    source="catalog",
                    duration_ms=210000,
                )
            )
    return results


def _search_catalog(query: str) -> list[ResolvedTrack]:
    needle = query.lower()
    hits = [
        track
        for track in catalog_tracks()
        if needle in track.name.lower() or needle in track.artist_name.lower() or needle in f"{track.artist_name} {track.name}".lower()
    ]
    return hits[:10]


def resolve_ref(db: Session, user: User, value: str) -> ResolvedTrack:
    kind, payload = parse_track_ref(value)
    client = catalog_client_for_user(db, user)
    if kind == "id" and payload and payload.startswith("syn-"):
        for track in catalog_tracks():
            if track.spotify_id == payload:
                return track
        raise ValueError("That demo track is not in the local catalog.")
    if kind == "id" and client:
        try:
            raw = client.get_track(payload)
            artist_id = (raw.get("artists") or [{}])[0].get("id")
            return _from_spotify_payload(raw, _hydrate_genres(client, artist_id))
        except SpotifyAPIError as exc:
            raise ValueError(str(exc)) from exc
    if kind == "id":
        raise ValueError(
            "Live Spotify lookup needs credentials. Add SPOTIFY_CLIENT_ID and SECRET to .env, or Connect Spotify."
        )
    query = payload or value
    if client:
        try:
            items = client.search_tracks(query, limit=10)
        except SpotifyAPIError:
            items = []
        if items:
            raw = items[0]
            artist_id = (raw.get("artists") or [{}])[0].get("id")
            return _from_spotify_payload(raw, _hydrate_genres(client, artist_id))
    hits = _search_catalog(query)
    if hits:
        return hits[0]
    raise ValueError("No matching track. Search a song name, or connect Spotify for the live catalog.")


def search_tracks(db: Session, user: User, query: str) -> list[ResolvedTrack]:
    if not query.strip():
        return catalog_tracks()[:24]
    client = catalog_client_for_user(db, user)
    results: list[ResolvedTrack] = []
    if client:
        try:
            for raw in client.search_tracks(query, limit=10):
                results.append(_from_spotify_payload(raw))
        except SpotifyAPIError:
            pass
    seen = {item.spotify_id for item in results}
    for item in _search_catalog(query):
        if item.spotify_id not in seen:
            results.append(item)
    return results[:12]


def _user_neighbor_artists(db: Session, user: User, artist_name: str) -> list[str]:
    rows = db.query(ArtistTransition).filter(ArtistTransition.user_id == user.id).all()
    names: list[str] = []
    for edge in rows:
        if edge.source_artist.name.lower() == artist_name.lower():
            names.append(edge.target_artist.name)
        elif edge.target_artist.name.lower() == artist_name.lower():
            names.append(edge.source_artist.name)
    # unique, keep order by count already roughly in table
    return list(dict.fromkeys(names))


def similar_tracks(db: Session, user: User, value: str, limit: int = 8) -> dict:
    seed = resolve_ref(db, user, value)
    client = catalog_client_for_user(db, user)
    candidates: list[ScoredTrack] = []
    seen = {seed.spotify_id, seed.name.lower()}

    def add(track: ResolvedTrack, reason: str, score: float) -> None:
        key = track.spotify_id
        if key in seen or (
            track.name.lower() == seed.name.lower() and track.artist_name.lower() == seed.artist_name.lower()
        ):
            return
        seen.add(key)
        candidates.append(ScoredTrack(track=track, reason=reason, score=score))

    if client:
        try:
            for raw in client.search_tracks(f'artist:"{seed.artist_name}"', limit=10):
                add(
                    _from_spotify_payload(raw, seed.genres),
                    f"Another track by {seed.artist_name} — same artist, not a trained model.",
                    0.9,
                )
        except SpotifyAPIError:
            pass
        for genre in seed.genres[:2]:
            try:
                for raw in client.search_tracks(f"genre:{genre}", limit=10):
                    add(
                        _from_spotify_payload(raw, [genre]),
                        f"Listed under the same Spotify artist genre (“{genre}”). This is metadata overlap, not audio similarity.",
                        0.55,
                    )
            except SpotifyAPIError:
                pass

    for track in catalog_tracks():
        if track.artist_name.lower() == seed.artist_name.lower():
            add(track, f"Another {seed.artist_name} track from the local catalog.", 0.85)
        elif set(track.genres) & set(seed.genres):
            shared = sorted(set(track.genres) & set(seed.genres))[0]
            add(track, f"Shares the “{shared}” genre tag with {seed.artist_name}.", 0.5)

    for neighbor in _user_neighbor_artists(db, user, seed.artist_name)[:6]:
        for track in catalog_tracks():
            if track.artist_name.lower() == neighbor.lower():
                add(
                    track,
                    f"In your listening sessions, {neighbor} often appears next to {seed.artist_name}.",
                    0.7,
                )
                break

    candidates.sort(key=lambda item: -item.score)
    return {
        "seed": seed.__dict__,
        "method": (
            "Transparent heuristic: same artist, shared Spotify genre tags, and (if you have a library) "
            "artists you actually move between in sessions. Not Spotify Radio, not audio features."
        ),
        "items": [{"reason": item.reason, "score": round(item.score, 3), **item.track.__dict__} for item in candidates[:limit]],
    }


def _genre_graph() -> nx.Graph:
    graph = nx.Graph()
    genres: dict[str, list[str]] = {}
    for entry in CATALOG:
        graph.add_node(entry["name"])
        genres[entry["name"]] = entry["genres"]
    for source, targets in FOLLOW.items():
        for target in targets:
            if graph.has_node(source) and graph.has_node(target):
                graph.add_edge(source, target, weight=1)
    # Shared genres create a softer hop so distant artists can still meet.
    names = list(genres)
    for i, left in enumerate(names):
        for right in names[i + 1 :]:
            shared = set(genres[left]) & set(genres[right])
            if shared and not graph.has_edge(left, right):
                graph.add_edge(left, right, weight=2)
    return graph


def _tracks_by_genre(client: SpotifyClient | None, genre: str, used: set[str]) -> list[ResolvedTrack]:
    found: list[ResolvedTrack] = []
    needle = genre.lower()
    if client:
        try:
            for raw in client.search_tracks(f'genre:"{genre}"', limit=8):
                track = _from_spotify_payload(raw, [genre])
                if track.spotify_id not in used:
                    found.append(track)
        except SpotifyAPIError:
            pass
    for track in catalog_tracks():
        if needle in [item.lower() for item in track.genres] and track.spotify_id not in used:
            found.append(track)
    return found


def _tracks_by_artist(client: SpotifyClient | None, artist_name: str, used: set[str]) -> list[ResolvedTrack]:
    found: list[ResolvedTrack] = []
    if client:
        try:
            for raw in client.search_tracks(f'artist:"{artist_name}"', limit=5):
                track = _from_spotify_payload(raw)
                if track.spotify_id not in used:
                    found.append(track)
        except SpotifyAPIError:
            pass
    for track in catalog_tracks():
        if track.artist_name.lower() == artist_name.lower() and track.spotify_id not in used:
            found.append(track)
    return found


def _step_payload(track: ResolvedTrack, role: str, reason: str) -> dict:
    return {**track.__dict__, "role": role, "reason": reason}


def bridge_playlist(
    db: Session,
    user: User,
    start_ref: str,
    end_ref: str,
    length: int = 7,
    unit: str = "songs",
) -> dict:
    start = resolve_ref(db, user, start_ref)
    end = resolve_ref(db, user, end_ref)
    if start.spotify_id == end.spotify_id:
        raise ValueError("Pick two different songs.")

    client = catalog_client_for_user(db, user)
    start_pace = pace_for_genres(start.genres)
    end_pace = pace_for_genres(end.genres)
    target_count = max(3, min(int(length), 16)) if unit != "minutes" else 8
    needed = max(0, target_count - 2)

    blocked_ids, blocked_artists, liked_artists = _taste(db, user)
    used = {start.spotify_id, end.spotify_id}
    middles: list[ResolvedTrack] = []
    waypoints = genre_waypoints(start.genres, end.genres, needed)
    path_note = (
        "Middle cards walk artist genre tags from the opening vibe toward the close "
        f"(pace {start_pace:.2f} → {end_pace:.2f}). This uses Get Artist genre metadata and Search, "
        "not Spotify Audio Features, BPM, or Radio. Thumbs-down tracks and artists are skipped; thumbs-up artists are preferred."
    )

    for genre in waypoints:
        options = _prefer(_tracks_by_genre(client, genre, used), blocked_ids, blocked_artists, liked_artists)
        if not options:
            options = _prefer(
                _tracks_by_artist(client, start.artist_name, used) or _tracks_by_artist(client, end.artist_name, used),
                blocked_ids,
                blocked_artists,
                liked_artists,
            )
        if not options:
            continue
        pick = options[0]
        used.add(pick.spotify_id)
        middles.append(pick)

    if unit == "minutes":
        target_ms = max(8, min(int(length), 90)) * 60 * 1000
        total = start.duration_ms + end.duration_ms + sum(track.duration_ms for track in middles)
        extra_pool = _tracks_by_genre(client, waypoints[-1] if waypoints else "pop", used)
        extra_pool.extend(_tracks_by_artist(client, end.artist_name, used))
        index = 0
        while total < target_ms and extra_pool and len(middles) < 16:
            candidate = extra_pool[index % len(extra_pool)]
            index += 1
            if candidate.spotify_id in used:
                if index > len(extra_pool) * 3:
                    break
                continue
            used.add(candidate.spotify_id)
            middles.append(candidate)
            total += candidate.duration_ms
        path_note += f" Length is about {round(total / 60000)} minutes of track duration from Spotify metadata."
    else:
        if len(middles) < needed:
            fallback = _tracks_by_artist(client, start.artist_name, used)
            fallback.extend(_tracks_by_artist(client, end.artist_name, used))
            for candidate in fallback:
                if len(middles) >= needed:
                    break
                if candidate.spotify_id in used:
                    continue
                used.add(candidate.spotify_id)
                middles.append(candidate)
        total = start.duration_ms + end.duration_ms + sum(track.duration_ms for track in middles)
        path_note += f" {2 + len(middles)} songs, about {round(total / 60000)} minutes."

    steps = [_step_payload(start, "start", "The opening card — the first song you picked.")]
    for index, track in enumerate(middles):
        genre = waypoints[index] if index < len(waypoints) else (track.genres[0] if track.genres else "adjacent")
        steps.append(
            _step_payload(
                track,
                "bridge",
                f"Genre step “{genre}” on the walk from {start.artist_name} toward {end.artist_name}.",
            )
        )
    steps.append(_step_payload(end, "end", "The closing card — the last song you picked."))

    total_ms = sum(int(step["duration_ms"]) for step in steps)
    return {
        "method": path_note,
        "unit": unit,
        "length": length,
        "song_count": len(steps),
        "duration_ms": total_ms,
        "duration_label": f"{round(total_ms / 60000)} min",
        "steps": steps,
        "start": start.__dict__,
        "end": end.__dict__,
    }
