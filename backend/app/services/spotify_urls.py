from __future__ import annotations

import re

SPOTIFY_TRACK_ID = re.compile(
    r"(?:open\.spotify\.com/track/|spotify:track:)([A-Za-z0-9]{22})",
    re.IGNORECASE,
)
BARE_TRACK_ID = re.compile(r"^[A-Za-z0-9]{22}$")
SYNTHETIC_ID = re.compile(r"^syn-[a-f0-9]{16}$")


def parse_track_ref(value: str) -> tuple[str, str | None]:
    """Return ('id', spotify_or_syn_id) or ('query', search_text)."""
    text = (value or "").strip()
    if not text:
        raise ValueError("Paste a Spotify track link, URI, or a song name.")
    match = SPOTIFY_TRACK_ID.search(text)
    if match:
        return "id", match.group(1)
    if BARE_TRACK_ID.fullmatch(text) or SYNTHETIC_ID.fullmatch(text):
        return "id", text
    return "query", text
