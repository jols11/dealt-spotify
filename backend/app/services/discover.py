from __future__ import annotations

from dataclasses import dataclass

import networkx as nx
from sqlalchemy.orm import Session

from app.models.entities import ArtistTransition, User
from app.services.auth import catalog_client_for_user
from app.services.demo_seed import CATALOG, FOLLOW
from app.services.spotify_client import SpotifyAPIError, SpotifyClient
from app.services.spotify_urls import parse_track_ref


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
    )


def _hydrate_genres(client: SpotifyClient, artist_id: str | None) -> list[str]:
    if not artist_id:
        return []
    try:
        artist = client.get_artist(artist_id)
    except SpotifyAPIError:
        return []
    return list(artist.get("genres") or [])


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
            genres = _hydrate_genres(client, (raw.get("artists") or [{}])[0].get("id"))
            return _from_spotify_payload(raw, genres)
        except SpotifyAPIError as exc:
            raise ValueError(str(exc)) from exc
    if kind == "id":
        raise ValueError(
            "A live Spotify link needs API credentials. Connect Spotify in Settings, or pick a catalog track below."
        )
    query = payload or value
    if client:
        try:
            items = client.search_tracks(query, limit=10)
        except SpotifyAPIError:
            items = []
        if items:
            raw = items[0]
            genres = _hydrate_genres(client, (raw.get("artists") or [{}])[0].get("id"))
            return _from_spotify_payload(raw, genres)
    hits = _search_catalog(query)
    if hits:
        return hits[0]
    raise ValueError("No matching track. Try a Spotify link, or a name from the demo catalog.")


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


def _track_for_artist(artist_name: str, used: set[str], preferred: ResolvedTrack | None = None) -> ResolvedTrack | None:
    if preferred and preferred.artist_name.lower() == artist_name.lower():
        return preferred
    for track in catalog_tracks():
        if track.artist_name.lower() == artist_name.lower() and track.spotify_id not in used:
            return track
    return None


def bridge_playlist(db: Session, user: User, start_ref: str, end_ref: str, length: int = 7) -> dict:
    if length < 3:
        length = 3
    if length > 12:
        length = 12
    start = resolve_ref(db, user, start_ref)
    end = resolve_ref(db, user, end_ref)
    if start.spotify_id == end.spotify_id:
        raise ValueError("Pick two different tracks.")

    graph = _genre_graph()
    # Overlay the listener's own handoffs as cheap edges.
    for edge in db.query(ArtistTransition).filter(ArtistTransition.user_id == user.id).all():
        a, b = edge.source_artist.name, edge.target_artist.name
        if graph.has_node(a) and graph.has_node(b):
            graph.add_edge(a, b, weight=0.5)

    start_artist, end_artist = start.artist_name, end.artist_name
    if start_artist not in graph:
        graph.add_node(start_artist)
    if end_artist not in graph:
        graph.add_node(end_artist)
    if start.genres and end.genres and set(start.genres) & set(end.genres):
        graph.add_edge(start_artist, end_artist, weight=1.5)

    try:
        artist_path = nx.shortest_path(graph, start_artist, end_artist, weight="weight")
        path_note = "Artist path is a shortest walk on genre overlap plus your session handoffs — not audio similarity."
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        artist_path = [start_artist, end_artist]
        path_note = "No overlapping-genre path was found, so this is a direct two-song frame with catalog neighbors filled in."

    # Stretch/compress the artist path to the requested length.
    mids_needed = length - 2
    expanded: list[str] = [artist_path[0]]
    if len(artist_path) == 1:
        artist_path = [start_artist, end_artist]
    inner = artist_path[1:-1]
    if not inner:
        # Fill with neighbors of start then end from FOLLOW / catalog genres
        for name in graph.neighbors(start_artist) if start_artist in graph else []:
            if name not in {start_artist, end_artist}:
                inner.append(name)
            if len(inner) >= mids_needed:
                break
    while len(inner) < mids_needed and inner:
        inner.append(inner[-1])
    inner = inner[:mids_needed]
    expanded.extend(inner)
    expanded.append(artist_path[-1])

    used: set[str] = set()
    steps = []
    for index, artist_name in enumerate(expanded):
        preferred = start if index == 0 else end if index == len(expanded) - 1 else None
        track = _track_for_artist(artist_name, used, preferred)
        if track is None:
            continue
        used.add(track.spotify_id)
        if index == 0:
            reason = "Your opening track."
        elif index == len(expanded) - 1:
            reason = "Your destination track."
        elif artist_name in FOLLOW.get(expanded[index - 1], []):
            reason = f"{expanded[index - 1]} often leads to {artist_name} in this catalog’s listening patterns."
        elif set(track.genres) & set(start.genres) and set(track.genres) & set(end.genres):
            reason = "Sits on genres shared with both the opening and the close."
        else:
            reason = f"A stepping stone via {artist_name} so the set does not jump straight from start to end."
        steps.append({**track.__dict__, "role": "start" if index == 0 else "end" if index == len(expanded) - 1 else "bridge", "reason": reason})

    if steps and steps[-1]["spotify_id"] != end.spotify_id:
        steps.append({**end.__dict__, "role": "end", "reason": "Your destination track."})

    return {
        "method": path_note,
        "steps": steps,
        "start": start.__dict__,
        "end": end.__dict__,
    }
