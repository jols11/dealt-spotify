from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.db.session import get_db
from app.models.entities import TrackFeedback, User

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class VoteRequest(BaseModel):
    spotify_id: str = Field(min_length=1, max_length=64)
    artist_name: str = ""
    genres: list[str] = Field(default_factory=list)
    vote: int = Field(ge=-1, le=1)


@router.get("")
def list_votes(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(TrackFeedback).filter(TrackFeedback.user_id == user.id).all()
    return {
        "items": [
            {
                "spotify_id": row.spotify_id,
                "artist_name": row.artist_name,
                "vote": row.vote,
            }
            for row in rows
        ]
    }


@router.post("")
def upsert_vote(body: VoteRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    row = (
        db.query(TrackFeedback)
        .filter(TrackFeedback.user_id == user.id, TrackFeedback.spotify_id == body.spotify_id)
        .one_or_none()
    )
    if body.vote == 0:
        if row is not None:
            db.delete(row)
            db.commit()
        return {"ok": True, "vote": 0}
    if row is None:
        row = TrackFeedback(
            user_id=user.id,
            spotify_id=body.spotify_id,
            artist_name=body.artist_name,
            genres=",".join(body.genres),
            vote=body.vote,
        )
        db.add(row)
    else:
        row.vote = body.vote
        row.artist_name = body.artist_name or row.artist_name
        if body.genres:
            row.genres = ",".join(body.genres)
    db.commit()
    return {"ok": True, "vote": row.vote}
