from __future__ import annotations

from sqlalchemy.orm import Session

from app.analytics.sessions import PlayRecord, sessionize
from app.analytics.transitions import transitions_from_sessions
from app.core.config import get_settings
from sqlalchemy.orm import joinedload

from app.models.entities import (
    Artist,
    ArtistGenre,
    ArtistTransition,
    ListeningEvent,
    ListeningSession,
    SessionEvent,
    Track,
    User,
)


def load_play_records(db: Session, user_id: int) -> list[PlayRecord]:
    rows = (
        db.query(ListeningEvent)
        .options(
            joinedload(ListeningEvent.track)
            .joinedload(Track.primary_artist)
            .joinedload(Artist.genres)
            .joinedload(ArtistGenre.genre)
        )
        .filter(ListeningEvent.user_id == user_id)
        .order_by(ListeningEvent.played_at.asc())
        .all()
    )
    records: list[PlayRecord] = []
    for event in rows:
        artist = event.track.primary_artist
        genre_name = None
        if artist.genres:
            genre_name = artist.genres[0].genre.name
        records.append(
            PlayRecord(
                event_id=event.id,
                track_id=event.track_id,
                artist_id=artist.id,
                artist_name=artist.name,
                track_name=event.track.name,
                played_at=event.played_at,
                genre=genre_name,
                album_name=event.track.album_name,
                album_image_url=event.track.album_image_url,
                duration_ms=event.track.duration_ms,
            )
        )
    return records


def rebuild_derived(db: Session, user: User) -> None:
    settings = get_settings()
    session_ids = [row[0] for row in db.query(ListeningSession.id).filter(ListeningSession.user_id == user.id).all()]
    if session_ids:
        db.query(SessionEvent).filter(SessionEvent.session_id.in_(session_ids)).delete(synchronize_session=False)
    db.query(ListeningSession).filter(ListeningSession.user_id == user.id).delete(synchronize_session=False)
    db.query(ArtistTransition).filter(ArtistTransition.user_id == user.id).delete(synchronize_session=False)
    db.flush()

    records = load_play_records(db, user.id)
    sessions = sessionize(records, gap_minutes=settings.session_gap_minutes)
    for session in sessions:
        stored = ListeningSession(
            user_id=user.id,
            start_time=session.start_time,
            end_time=session.end_time,
            track_count=session.track_count,
            unique_artist_count=session.unique_artist_count,
            dominant_artist_id=session.dominant_artist_id,
            dominant_genre=session.dominant_genre,
            duration_seconds=session.duration_seconds,
        )
        db.add(stored)
        db.flush()
        for position, event in enumerate(session.events):
            if event.event_id is None:
                continue
            db.add(SessionEvent(session_id=stored.id, event_id=event.event_id, position=position))

    for edge in transitions_from_sessions(sessions):
        db.add(
            ArtistTransition(
                user_id=user.id,
                source_artist_id=edge.source_artist_id,
                target_artist_id=edge.target_artist_id,
                transition_count=edge.count,
                transition_probability=edge.probability,
            )
        )
    db.commit()
