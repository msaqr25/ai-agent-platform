from __future__ import annotations

MIME_TO_EXT: dict[str, str] = {
    "audio/wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/ogg": ".ogg",
    "audio/webm": ".webm",
}

ALLOWED_AUDIO_MIME_TYPES: frozenset[str] = frozenset(MIME_TO_EXT)
