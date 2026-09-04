from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spotify_account_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255), default="Listener")
    country: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    product: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    tokens: Mapped[list["OAuthToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    listening_events: Mapped[list["ListeningEvent"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    sessions: Mapped[list["ListeningSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    transitions: Mapped[list["ArtistTransition"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    top_snapshots: Mapped[list["TopSnapshot"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    scopes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship(back_populates="tokens")


class Artist(Base):
    __tablename__ = "artists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spotify_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    popularity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    follower_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    genres: Mapped[list["ArtistGenre"]] = relationship(back_populates="artist", cascade="all, delete-orphan")


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, index=True)


class ArtistGenre(Base):
    __tablename__ = "artist_genres"
    __table_args__ = (UniqueConstraint("artist_id", "genre_id", name="uq_artist_genre"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id", ondelete="CASCADE"), index=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id", ondelete="CASCADE"), index=True)

    artist: Mapped[Artist] = relationship(back_populates="genres")
    genre: Mapped[Genre] = relationship()


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spotify_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(512))
    album_name: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    album_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    popularity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    primary_artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id"), index=True)

    primary_artist: Mapped[Artist] = relationship()
    credits: Mapped[list["TrackArtist"]] = relationship(back_populates="track", cascade="all, delete-orphan")


class TrackArtist(Base):
    __tablename__ = "track_artists"
    __table_args__ = (UniqueConstraint("track_id", "artist_id", name="uq_track_artist"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), index=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)

    track: Mapped[Track] = relationship(back_populates="credits")
    artist: Mapped[Artist] = relationship()


class ListeningEvent(Base):
    __tablename__ = "listening_events"
    __table_args__ = (
        UniqueConstraint("user_id", "track_id", "played_at", name="uq_user_track_played_at"),
        Index("ix_events_user_played_at", "user_id", "played_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id"), index=True)
    played_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    context_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    context_uri: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    user: Mapped[User] = relationship(back_populates="listening_events")
    track: Mapped[Track] = relationship()


class ListeningSession(Base):
    __tablename__ = "listening_sessions"
    __table_args__ = (Index("ix_sessions_user_start", "user_id", "start_time"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    track_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_artist_count: Mapped[int] = mapped_column(Integer, default=0)
    dominant_artist_id: Mapped[Optional[int]] = mapped_column(ForeignKey("artists.id"), nullable=True)
    dominant_genre: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped[User] = relationship(back_populates="sessions")
    dominant_artist: Mapped[Optional[Artist]] = relationship()
    members: Mapped[list["SessionEvent"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class SessionEvent(Base):
    __tablename__ = "session_events"
    __table_args__ = (UniqueConstraint("session_id", "event_id", name="uq_session_event"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("listening_sessions.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("listening_events.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)

    session: Mapped[ListeningSession] = relationship(back_populates="members")
    event: Mapped[ListeningEvent] = relationship()


class ArtistTransition(Base):
    __tablename__ = "artist_transitions"
    __table_args__ = (
        UniqueConstraint("user_id", "source_artist_id", "target_artist_id", name="uq_user_transition"),
        Index("ix_transitions_user_source", "user_id", "source_artist_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source_artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id"), index=True)
    target_artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id"), index=True)
    transition_count: Mapped[int] = mapped_column(Integer, default=0)
    transition_probability: Mapped[float] = mapped_column(Float, default=0.0)

    user: Mapped[User] = relationship(back_populates="transitions")
    source_artist: Mapped[Artist] = relationship(foreign_keys=[source_artist_id])
    target_artist: Mapped[Artist] = relationship(foreign_keys=[target_artist_id])


class TopSnapshot(Base):
    """Taste snapshots from /me/top. These are not play events."""

    __tablename__ = "top_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "item_type",
            "time_range",
            "rank",
            "fetched_at",
            name="uq_top_snapshot_rank",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    item_type: Mapped[str] = mapped_column(String(16))  # artist | track
    time_range: Mapped[str] = mapped_column(String(16))  # short_term | medium_term | long_term
    rank: Mapped[int] = mapped_column(Integer)
    item_spotify_id: Mapped[str] = mapped_column(String(64), index=True)
    item_name: Mapped[str] = mapped_column(String(512))
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="top_snapshots")
