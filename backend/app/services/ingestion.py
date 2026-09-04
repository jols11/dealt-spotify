from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import Artist, ArtistGenre, Genre, ListeningEvent, Track, TrackArtist, User
from app.services.spotify_client import SpotifyClient


def _image_url(images: list[dict[str, Any]] | None) -> str | None:
    if not images:
        return None
    return images[0].get("url")


def upsert_artist(db: Session, payload: dict[str, Any]) -> Artist:
    spotify_id = payload["id"]
    artist = db.query(Artist).filter(Artist.spotify_id == spotify_id).one_or_none()
    if artist is None:
        artist = Artist(spotify_id=spotify_id, name=payload.get("name") or "Unknown artist")
        db.add(artist)
        db.flush()
    artist.name = payload.get("name") or artist.name
    if payload.get("popularity") is not None:
        artist.popularity = payload.get("popularity")
    if payload.get("images"):
        artist.image_url = _image_url(payload.get("images"))
    followers = payload.get("followers") or {}
    if followers.get("total") is not None:
        artist.follower_count = followers.get("total")
    for genre_name in payload.get("genres") or []:
        genre = db.query(Genre).filter(Genre.name == genre_name).one_or_none()
        if genre is None:
            genre = Genre(name=genre_name)
            db.add(genre)
            db.flush()
        link = (
            db.query(ArtistGenre)
            .filter(ArtistGenre.artist_id == artist.id, ArtistGenre.genre_id == genre.id)
            .one_or_none()
        )
        if link is None:
            db.add(ArtistGenre(artist_id=artist.id, genre_id=genre.id))
    db.flush()
    return artist


def upsert_track(db: Session, payload: dict[str, Any]) -> Track | None:
    spotify_id = payload.get("id")
    if not spotify_id:
        return None
    artists_payload = payload.get("artists") or []
    if not artists_payload:
        return None
    primary = upsert_artist(db, artists_payload[0])
    album = payload.get("album") or {}
    track = db.query(Track).filter(Track.spotify_id == spotify_id).one_or_none()
    if track is None:
        track = Track(
            spotify_id=spotify_id,
            name=payload.get("name") or "Unknown track",
            album_name=album.get("name"),
            album_image_url=_image_url(album.get("images")),
            duration_ms=payload.get("duration_ms"),
            popularity=payload.get("popularity"),
            primary_artist_id=primary.id,
        )
        db.add(track)
        db.flush()
    else:
        track.name = payload.get("name") or track.name
        track.album_name = album.get("name") or track.album_name
        track.album_image_url = _image_url(album.get("images")) or track.album_image_url
        track.primary_artist_id = primary.id
    for position, artist_payload in enumerate(artists_payload):
        artist = upsert_artist(db, artist_payload)
        existing = (
            db.query(TrackArtist)
            .filter(TrackArtist.track_id == track.id, TrackArtist.artist_id == artist.id)
            .one_or_none()
        )
        if existing is None:
            db.add(TrackArtist(track_id=track.id, artist_id=artist.id, position=position))
    db.flush()
    return track


def parse_played_at(value: str) -> datetime:
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp


def ingest_recently_played(db: Session, user: User, items: list[dict[str, Any]]) -> int:
    inserted = 0
    for item in items:
        track_payload = item.get("track") or {}
        played_at_raw = item.get("played_at")
        if not played_at_raw:
            continue
        track = upsert_track(db, track_payload)
        if track is None:
            continue
        context = item.get("context") or {}
        played_at = parse_played_at(played_at_raw)
        exists = (
            db.query(ListeningEvent)
            .filter(
                ListeningEvent.user_id == user.id,
                ListeningEvent.track_id == track.id,
                ListeningEvent.played_at == played_at,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            ListeningEvent(
                user_id=user.id,
                track_id=track.id,
                played_at=played_at,
                context_type=context.get("type"),
                context_uri=context.get("uri"),
            )
        )
        inserted += 1
    db.commit()
    return inserted


def hydrate_artist_metadata(db: Session, client: SpotifyClient, artist_spotify_ids: list[str]) -> None:
    if not artist_spotify_ids:
        return
    for artist_payload in client.artists(artist_spotify_ids):
        if artist_payload:
            upsert_artist(db, artist_payload)
    db.commit()


def ingest_top_snapshots(db: Session, user: User, client: SpotifyClient) -> None:
    from app.models.entities import TopSnapshot

    fetched_at = datetime.now(timezone.utc)
    for item_type in ("artists", "tracks"):
        for time_range in ("short_term", "medium_term", "long_term"):
            payload = client.top_items(item_type, time_range)
            for rank, item in enumerate(payload.get("items") or [], start=1):
                if item_type == "artists":
                    upsert_artist(db, item)
                    name = item.get("name") or "Unknown"
                    spotify_id = item["id"]
                else:
                    track = upsert_track(db, item)
                    if track is None:
                        continue
                    name = track.name
                    spotify_id = track.spotify_id
                db.add(
                    TopSnapshot(
                        user_id=user.id,
                        item_type="artist" if item_type == "artists" else "track",
                        time_range=time_range,
                        rank=rank,
                        item_spotify_id=spotify_id,
                        item_name=name,
                        fetched_at=fetched_at,
                    )
                )
    db.commit()
