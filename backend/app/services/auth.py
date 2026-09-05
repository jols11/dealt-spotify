from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decrypt_token, encrypt_token, generate_code_challenge, generate_code_verifier, generate_state
from app.models.entities import OAuthToken, User
from app.services.spotify_client import SpotifyAPIError, SpotifyClient


class AuthError(Exception):
    pass


def build_authorize_url(session: dict[str, Any]) -> str:
    settings = get_settings()
    if not settings.spotify_client_id:
        raise AuthError("SPOTIFY_CLIENT_ID is not configured. Use demo mode or add credentials.")
    verifier = generate_code_verifier()
    state = generate_state()
    session["pkce_verifier"] = verifier
    session["oauth_state"] = state
    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.redirect_uri_effective,
        "scope": settings.oauth_scopes,
        "state": state,
        "code_challenge_method": "S256",
        "code_challenge": generate_code_challenge(verifier),
    }
    return f"{settings.spotify_auth_url}?{urlencode(params)}"


def exchange_code(code: str, verifier: str) -> dict[str, Any]:
    settings = get_settings()
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.redirect_uri_effective,
        "client_id": settings.spotify_client_id,
        "code_verifier": verifier,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if settings.spotify_client_secret:
        auth = (settings.spotify_client_id, settings.spotify_client_secret)
    else:
        auth = None
    try:
        response = httpx.post(settings.spotify_token_url, data=data, headers=headers, auth=auth, timeout=20.0)
    except httpx.HTTPError as exc:
        raise AuthError(f"Could not reach Spotify token endpoint: {exc}") from exc
    if response.status_code >= 400:
        raise AuthError(f"Token exchange failed: {response.text[:300]}")
    return response.json()


def refresh_access_token(refresh_token: str) -> dict[str, Any]:
    settings = get_settings()
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": settings.spotify_client_id,
    }
    auth = None
    if settings.spotify_client_secret:
        auth = (settings.spotify_client_id, settings.spotify_client_secret)
    response = httpx.post(settings.spotify_token_url, data=data, auth=auth, timeout=20.0)
    if response.status_code >= 400:
        raise AuthError("Refresh token was rejected. Please reconnect Spotify.")
    return response.json()


def upsert_user_from_profile(db: Session, profile: dict[str, Any], is_demo: bool = False) -> User:
    images = profile.get("images") or []
    image_url = images[0]["url"] if images else None
    spotify_id = profile["id"]
    user = db.query(User).filter(User.spotify_account_id == spotify_id).one_or_none()
    if user is None:
        user = User(spotify_account_id=spotify_id)
        db.add(user)
    user.display_name = profile.get("display_name") or profile.get("id") or "Listener"
    user.country = profile.get("country")
    user.product = profile.get("product")
    user.image_url = image_url
    user.is_demo = is_demo
    db.flush()
    return user


def store_tokens(db: Session, user: User, token_payload: dict[str, Any]) -> None:
    expires_in = int(token_payload.get("expires_in") or 3600)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in - 30)
    existing = db.query(OAuthToken).filter(OAuthToken.user_id == user.id).one_or_none()
    refresh = token_payload.get("refresh_token")
    if existing is None:
        existing = OAuthToken(user_id=user.id)
        db.add(existing)
    existing.access_token = encrypt_token(token_payload["access_token"])
    if refresh:
        existing.refresh_token = encrypt_token(refresh)
    existing.expires_at = expires_at
    existing.scopes = token_payload.get("scope")
    db.flush()


def get_valid_access_token(db: Session, user: User) -> str:
    token = db.query(OAuthToken).filter(OAuthToken.user_id == user.id).one_or_none()
    if token is None:
        raise AuthError("No Spotify tokens stored for this account.")
    now = datetime.now(timezone.utc)
    expires = token.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires > now:
        return decrypt_token(token.access_token)
    if not token.refresh_token:
        raise AuthError("Access token expired and no refresh token is available.")
    payload = refresh_access_token(decrypt_token(token.refresh_token))
    store_tokens(db, user, payload)
    return decrypt_token(token.access_token)


def complete_oauth(db: Session, code: str, state: str, session: dict[str, Any]) -> User:
    expected = session.get("oauth_state")
    verifier = session.get("pkce_verifier")
    if not expected or state != expected or not verifier:
        raise AuthError("OAuth state mismatch. Start login again.")
    payload = exchange_code(code, verifier)
    access = payload.get("access_token")
    if not access:
        raise AuthError("Spotify did not return an access token.")
    profile = SpotifyClient(access).current_user()
    user = upsert_user_from_profile(db, profile, is_demo=False)
    store_tokens(db, user, payload)
    db.commit()
    session.pop("oauth_state", None)
    session.pop("pkce_verifier", None)
    return user


_catalog_token: str | None = None
_catalog_expires: datetime | None = None


def client_credentials_token() -> str | None:
    """App-only token for public catalog lookup (search / get track), not user history."""
    global _catalog_token, _catalog_expires
    settings = get_settings()
    if not settings.spotify_client_id or not settings.spotify_client_secret:
        return None
    now = datetime.now(timezone.utc)
    if _catalog_token and _catalog_expires and _catalog_expires > now:
        return _catalog_token
    try:
        response = httpx.post(
            settings.spotify_token_url,
            data={"grant_type": "client_credentials"},
            auth=(settings.spotify_client_id, settings.spotify_client_secret),
            timeout=20.0,
        )
    except httpx.HTTPError:
        return None
    if response.status_code >= 400:
        return None
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        return None
    _catalog_token = token
    _catalog_expires = now + timedelta(seconds=int(payload.get("expires_in") or 3600) - 60)
    return _catalog_token


def catalog_client_for_user(db: Session, user: User) -> SpotifyClient | None:
    if not user.is_demo:
        try:
            return SpotifyClient(get_valid_access_token(db, user))
        except AuthError:
            pass
    token = client_credentials_token()
    if token:
        return SpotifyClient(token)
    return None
