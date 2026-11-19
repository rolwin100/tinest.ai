"""Logical voice_id -> (backend, backend voice).

This resolution is deliberately server-side. Reference audio, reference text and
speaker embeddings never travel in a request (ADR 0004), so the client only ever
knows a stable name like `hi-female-01`.
"""

import os
from pathlib import Path

import yaml
from pydantic import BaseModel

from gotiny.core.logging import get_logger

log = get_logger("gotiny.tts.voices")

DEFAULT_PATH = Path(__file__).resolve().parents[1] / "config" / "voices.yaml"


class VoiceSpec(BaseModel):
    model_config = {"frozen": True}

    voice_id: str
    backend: str
    voice: str
    language: str
    grade: str | None = None
    note: str | None = None


def _read(p: Path) -> dict[str, VoiceSpec]:
    raw = yaml.safe_load(p.read_text()) or {}
    specs = {
        vid: VoiceSpec(voice_id=vid, **cfg) for vid, cfg in (raw.get("voices") or {}).items()
    }
    if not specs:
        raise ValueError(f"no voices defined in {p}")
    return specs


class VoiceRegistry:
    """The voice table, re-read when the file on disk changes.

    Why hot-reload a config file a restart would also pick up: because a restart
    also re-loads the weights. Tuning a Qwen3-TTS ``instruct`` string is an
    edit-listen-edit loop, and paying a 1.2 GB model load to change one adjective
    makes that loop unusable. This table is a few hundred bytes of text and holds
    no model state, so it can be re-read on its own.

    A broken edit must not take synthesis down. If the file fails to parse --
    which is exactly what a half-saved file looks like -- the previous table
    stays live and the error is logged.
    """

    def __init__(self, specs: dict[str, VoiceSpec], path: Path | None = None) -> None:
        self._specs = specs
        self._path = path
        self._mtime = path.stat().st_mtime if path else None

    @classmethod
    def load(cls, path: Path | None = None) -> "VoiceRegistry":
        p = path or Path(os.getenv("GOTINY_TTS_VOICES", DEFAULT_PATH))
        return cls(_read(p), p)

    def maybe_reload(self) -> bool:
        """Re-read if the file changed. Returns True if the table was replaced."""
        if self._path is None:
            return False
        try:
            mtime = self._path.stat().st_mtime
        except OSError:
            return False
        if mtime == self._mtime:
            return False
        self._mtime = mtime
        try:
            specs = _read(self._path)
        except Exception as e:  # noqa: BLE001 - a bad edit keeps the last good table
            log.warning("voices_reload_failed", path=str(self._path), error=str(e))
            return False
        added = sorted(set(specs) - set(self._specs))
        removed = sorted(set(self._specs) - set(specs))
        self._specs = specs
        log.info("voices_reloaded", count=len(specs), added=added, removed=removed)
        return True

    def get(self, voice_id: str) -> VoiceSpec:
        try:
            return self._specs[voice_id]
        except KeyError:
            raise KeyError(f"unknown voice_id {voice_id!r}; known: {sorted(self._specs)}") from None

    def all(self) -> list[VoiceSpec]:
        return list(self._specs.values())
