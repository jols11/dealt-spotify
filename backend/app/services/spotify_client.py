from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SpotifyAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None, retry_after: int | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


class SpotifyClient:
    """Thin Spotify Web API client using currently documented user endpoints.

    Intentionally omitted: audio features, audio analysis, and recommendations.
    """

    def __init__(self, access_token: str, timeout: float = 8.0):
        self.access_token = access_token
        self.settings = get_settings()
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    def _request(self, method: str, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.settings.spotify_api_base}{path}"
        retries = 0
        while True:
            try:
                response = httpx.request(
                    method,
                    url,
                    params=params,
                    headers=self._headers(),
                    timeout=self.timeout,
                )
            except httpx.HTTPError as exc:
                raise SpotifyAPIError(f"Network error talking to Spotify: {exc}") from exc

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", "1"))
                retries += 1
                if retries > 3:
                    raise SpotifyAPIError("Spotify rate limit persisted after retries.", 429, retry_after)
                logger.warning("Spotify 429; sleeping %s seconds", retry_after)
                time.sleep(min(retry_after, 1))
                continue

            if response.status_code >= 400:
                detail = response.text[:400]
                raise SpotifyAPIError(
                    f"Spotify API error {response.status_code}: {detail}",
                    status_code=response.status_code,
                )
            if not response.content:
                return {}
            return response.json()

    def current_user(self) -> dict[str, Any]:
        return self._request("GET", "/me")

    def recently_played(self, limit: int = 50, before: str | None = None, after: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"limit": min(limit, 50)}
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        return self._request("GET", "/me/player/recently-played", params=params)

    def paginate_recently_played(self, max_pages: int = 4) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        before: str | None = None
        for _ in range(max_pages):
            payload = self.recently_played(limit=50, before=before)
            batch = payload.get("items") or []
            if not batch:
                break
            items.extend(batch)
            cursors = payload.get("cursors") or {}
            next_before = cursors.get("before")
            if not next_before or not payload.get("next"):
                break
            before = next_before
        return items

    def top_items(self, item_type: str, time_range: str, limit: int = 50) -> dict[str, Any]:
        assert item_type in {"artists", "tracks"}
        return self._request(
            "GET",
            f"/me/top/{item_type}",
            params={"time_range": time_range, "limit": min(limit, 50)},
        )

    def artists(self, spotify_ids: list[str]) -> list[dict[str, Any]]:
        artists: list[dict[str, Any]] = []
        unique_ids = list(dict.fromkeys(spotify_ids))
        for index in range(0, len(unique_ids), 50):
            chunk = unique_ids[index : index + 50]
            payload = self._request("GET", "/artists", params={"ids": ",".join(chunk)})
            artists.extend(payload.get("artists") or [])
        return artists

    def get_track(self, spotify_id: str) -> dict[str, Any]:
        return self._request("GET", f"/tracks/{spotify_id}")

    def get_artist(self, spotify_id: str) -> dict[str, Any]:
        return self._request("GET", f"/artists/{spotify_id}")

    def search_tracks(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        # New Spotify apps often cap search limit at 10 even if docs say 50.
        payload = self._request(
            "GET",
            "/search",
            params={"q": query, "type": "track", "limit": min(max(limit, 1), 10)},
        )
        return ((payload.get("tracks") or {}).get("items")) or []
