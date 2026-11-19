"""What the agent is: prompt, voice, language, tools, turn-taking.

Loaded from ``deploy/seeds/*.yaml`` today. In week 2 this becomes an
``agent_version`` row and the file becomes an import fixture (ADR 0003) -- so the
loader is deliberately shaped as "give me a dict, get a validated Persona",
which makes that a change of source rather than a change of shape.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from gotiny.core.paths import find_repo_root
from gotiny.core.types import Language

def _default_seed() -> Path:
    """Resolve the persona file against the repo root, not the working directory.

    Same trap as .env: a relative default silently points somewhere else the
    moment a process starts from a subdirectory.
    """
    configured = os.getenv("GOTINY_PERSONA", "deploy/seeds/receptionist.yaml")
    path = Path(configured)
    if path.is_absolute():
        return path
    root = find_repo_root()
    return (root / path) if root else path


class TurnConfig(BaseModel):
    """End-of-turn detection.

    The single largest line in the latency budget, and it is tuning rather than
    code -- which is why it is persona config and not a constant. Too short and
    the agent interrupts; too long and every reply feels sluggish.
    """

    model_config = {"frozen": True}

    stop_secs: float = Field(default=0.6, description="Silence before we call the turn over.")
    start_secs: float = Field(default=0.2, description="Speech before we believe it is speech.")
    confidence: float = 0.7
    min_volume: float = 0.6


class Persona(BaseModel):
    model_config = {"frozen": True}

    slug: str
    name: str
    language: Language
    voice_id: str
    speed: float = Field(
        default=1.0,
        gt=0.5,
        lt=2.0,
        description="Speaking rate multiplier. 1.0 is the voice's own pace; "
        "1.15 is noticeably brisker without sounding chipmunked. Kokoro takes "
        "this as a number; Qwen3-TTS has no rate parameter, so its backend "
        "turns it into words in the style instruction.",
    )
    prompt: str
    greeting: str
    tools: list[str] = Field(default_factory=list)
    turn: TurnConfig = Field(default_factory=TurnConfig)
    ai_disclosure: str | None = Field(
        default=None,
        description="Spoken at call start. Cheap now; a migration and a "
        "contract renegotiation later. See IT Rules 2026 on synthetic media.",
    )

    @classmethod
    def from_dict(cls, slug: str, data: dict[str, Any]) -> "Persona":
        return cls(slug=slug, **data)

    @classmethod
    def load(cls, path: Path | None = None) -> "Persona":
        p = path or _default_seed()
        raw = yaml.safe_load(p.read_text())
        if not raw:
            raise ValueError(f"empty persona file: {p}")
        slug = raw.pop("slug", p.stem)
        return cls.from_dict(slug, raw)

    def opening(self) -> str:
        """What the agent says first, spoken deterministically -- not prompted.

        The disclosure used to be an instruction at the end of the system prompt
        ("say exactly: ..."). A 4B model treated the last thing it was told as
        the most important thing it was told, and repeated the disclosure instead
        of answering. Worse, a *prompted* disclosure is one the model can decline
        to say -- and this is a legal statement, not a stylistic preference. So it
        is spoken as text, straight to TTS, with the model uninvolved.
        """
        return " ".join(part for part in (self.ai_disclosure, self.greeting) if part)

    def system_message(self, now: datetime | None = None) -> str:
        """The prompt, plus the one fact a language model cannot know.

        Without this, "what time is it?" is unanswerable -- the model has no
        clock, and on a phone call that is a question people genuinely ask. It is
        injected at call start rather than fetched through a tool because a tool
        round-trip costs a second for something we already know.
        """
        stamp = (now or datetime.now().astimezone()).strftime("%A %d %B %Y, %I:%M %p (%Z)")
        return (
            f"{self.prompt}\n\nRight now it is {stamp}. "
            f"Use this for any question about the date or time."
        )
