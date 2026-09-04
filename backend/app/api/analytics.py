from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.analytics.graph import build_transition_graph
from app.analytics.sessions import sessionize
from app.analytics.transitions import transitions_from_sessions
from app.core.config import get_settings
from app.db.session import get_db
from app.models.entities import User
from app.services.analytics_service import assemble_analytics
from app.services.pipeline import load_play_records

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _require_payload(db: Session, user: User) -> dict:
    payload = assemble_analytics(db, user)
    return payload


@router.get("/overview")
def overview(db: Session = Depends(get_db), user: User = Depends(current_user)):
    payload = _require_payload(db, user)
    return {
        "user": payload["user"],
        **payload["overview"],
        "sessions_preview": payload["sessions"],
    }


@router.get("/evolution")
def evolution(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _require_payload(db, user)["evolution"]


@router.get("/transitions")
def transitions(
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
    min_count: int = Query(default=2, ge=1),
    artist_id: int | None = None,
    max_edges: int = Query(default=36, ge=4, le=80),
):
    settings = get_settings()
    events = load_play_records(db, user.id)
    sessions = sessionize(events, gap_minutes=settings.session_gap_minutes)
    edges = transitions_from_sessions(sessions)
    from collections import Counter

    play_counts = Counter(event.artist_id for event in events)
    names = {event.artist_id: event.artist_name for event in events}
    graph = build_transition_graph(
        edges,
        dict(play_counts),
        names,
        min_count=min_count,
        max_edges=max_edges,
        focus_artist_id=artist_id,
    )
    return {
        "insight": graph.insight,
        "nodes": [node.__dict__ for node in graph.nodes],
        "edges": graph.edges,
        "transitions": _require_payload(db, user)["network"]["transitions"],
    }


@router.get("/time-patterns")
def time_patterns(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _require_payload(db, user)["patterns"]


@router.get("/diversity")
def diversity(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _require_payload(db, user)["taste"]["diversity"]


@router.get("/clusters")
def clusters(db: Session = Depends(get_db), user: User = Depends(current_user)):
    taste = _require_payload(db, user)["taste"]
    return {"clusters": taste["clusters"], "top_artists": taste["top_artists"], "similarity": taste["similarity"]}


@router.get("/recommendations")
def recommendations(db: Session = Depends(get_db), user: User = Depends(current_user)):
    items = _require_payload(db, user)["recommendations"]
    return {
        "items": items,
        "empty": not items,
        "message": None
        if items
        else "No revisit suggestions yet. This heuristic needs a longer history with artists that have gone quiet.",
    }


@router.get("/taste")
def taste(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _require_payload(db, user)["taste"]
