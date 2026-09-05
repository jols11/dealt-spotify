from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.entities import ArtistTransition, User
from app.services.auth import AuthError, build_authorize_url, complete_oauth
from app.services.demo_seed import generate_demo_events
from app.services.pipeline import rebuild_derived

router = APIRouter(prefix="/api/auth", tags=["auth"])


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not signed in.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Session is no longer valid.")
    return user


def optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.get(User, user_id)


@router.get("/login")
def login(request: Request):
    try:
        url = build_authorize_url(request.session)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"url": url}


@router.get("/callback")
def callback(request: Request, db: Session = Depends(get_db), code: str | None = None, state: str | None = None, error: str | None = None):
    settings = get_settings()
    frontend = settings.frontend_origin_effective
    if error:
        return RedirectResponse(f"{frontend}/?error={error}")
    if not code or not state:
        return RedirectResponse(f"{frontend}/?error=missing_code")
    try:
        user = complete_oauth(db, code, state, request.session)
    except AuthError as exc:
        return RedirectResponse(f"{frontend}/?error=oauth")
    request.session["user_id"] = user.id
    return RedirectResponse(f"{frontend}/?connected=1")


@router.post("/demo")
def enter_demo(request: Request, db: Session = Depends(get_db)):
    existing = optional_user(request, db)
    if existing:
        request.session["user_id"] = existing.id
        return {"ok": True, "display_name": existing.display_name, "is_demo": existing.is_demo}
    user = generate_demo_events(db)
    if db.query(ArtistTransition).filter(ArtistTransition.user_id == user.id).count() == 0:
        rebuild_derived(db, user)
    request.session["user_id"] = user.id
    request.session["demo"] = True
    return {"ok": True, "display_name": user.display_name, "is_demo": True}


@router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    user = optional_user(request, db)
    settings = get_settings()
    configured = settings.spotify_configured
    catalog_ready = settings.catalog_ready
    if user is None:
        return {
            "authenticated": False,
            "user": None,
            "spotify_configured": configured,
            "catalog_ready": catalog_ready,
        }
    return {
        "authenticated": True,
        "spotify_configured": configured,
        "catalog_ready": catalog_ready or not user.is_demo,
        "user": {
            "id": user.id,
            "display_name": user.display_name,
            "is_demo": user.is_demo,
            "image_url": user.image_url,
        },
    }


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}
