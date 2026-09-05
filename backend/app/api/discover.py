from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.db.session import get_db
from app.models.entities import User
from app.services.discover import bridge_playlist, catalog_tracks, search_tracks, similar_tracks

router = APIRouter(prefix="/api/discover", tags=["discover"])


class SimilarRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class BridgeRequest(BaseModel):
    start: str = Field(min_length=1, max_length=500)
    end: str = Field(min_length=1, max_length=500)
    unit: Literal["songs", "minutes"] = "songs"
    length: int = Field(default=7, ge=3, le=90)


@router.get("/catalog")
def catalog(_user: User = Depends(current_user)):
    return {"items": [item.__dict__ for item in catalog_tracks()]}


@router.get("/search")
def search(q: str = Query(default=""), db: Session = Depends(get_db), user: User = Depends(current_user)):
    return {"items": [item.__dict__ for item in search_tracks(db, user, q)]}


@router.post("/similar")
def similar(body: SimilarRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    try:
        return similar_tracks(db, user, body.query)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/bridge")
def bridge(body: BridgeRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    try:
        return bridge_playlist(db, user, body.start, body.end, body.length, body.unit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not finish this deal. Check that the API is running and Spotify credentials are valid, then try again.",
        ) from exc
