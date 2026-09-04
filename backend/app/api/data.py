from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.db.session import get_db
from app.models.entities import (
    ArtistTransition,
    ListeningEvent,
    ListeningSession,
    OAuthToken,
    SessionEvent,
    TopSnapshot,
    User,
)
from app.services.auth import AuthError, get_valid_access_token
from app.services.ingestion import hydrate_artist_metadata, ingest_recently_played, ingest_top_snapshots
from app.services.pipeline import rebuild_derived
from app.services.spotify_client import SpotifyAPIError, SpotifyClient

router = APIRouter(prefix="/api/data", tags=["data"])


@router.post("/sync")
def sync_spotify(request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.is_demo:
        rebuild_derived(db, user)
        return {
            "ok": True,
            "mode": "demo",
            "inserted": 0,
            "message": "Demo library is synthetic and already loaded. Derived metrics were rebuilt.",
        }
    try:
        token = get_valid_access_token(db, user)
        client = SpotifyClient(token)
        items = client.paginate_recently_played()
        inserted = ingest_recently_played(db, user, items)
        artist_ids = []
        for item in items:
            for artist in (item.get("track") or {}).get("artists") or []:
                if artist.get("id"):
                    artist_ids.append(artist["id"])
        hydrate_artist_metadata(db, client, artist_ids)
        ingest_top_snapshots(db, user, client)
        rebuild_derived(db, user)
        return {
            "ok": True,
            "mode": "spotify",
            "inserted": inserted,
            "recently_played_fetched": len(items),
            "note": "Spotify only exposes a short recently-played window. Top artists/tracks are stored as taste snapshots, not extra play events.",
        }
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except SpotifyAPIError as exc:
        status = 429 if exc.status_code == 429 else 502
        raise HTTPException(status_code=status, detail=str(exc)) from exc


@router.delete("/me")
def clear_my_data(request: Request, db: Session = Depends(get_db), user: User = Depends(current_user)):
    db.query(SessionEvent).filter(
        SessionEvent.session_id.in_(db.query(ListeningSession.id).filter(ListeningSession.user_id == user.id))
    ).delete(synchronize_session=False)
    db.query(ListeningSession).filter(ListeningSession.user_id == user.id).delete(synchronize_session=False)
    db.query(ArtistTransition).filter(ArtistTransition.user_id == user.id).delete(synchronize_session=False)
    db.query(ListeningEvent).filter(ListeningEvent.user_id == user.id).delete(synchronize_session=False)
    db.query(TopSnapshot).filter(TopSnapshot.user_id == user.id).delete(synchronize_session=False)
    db.query(OAuthToken).filter(OAuthToken.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()
    request.session.clear()
    return {"ok": True}
