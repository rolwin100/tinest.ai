"""What a provider claims it can do.

Capabilities are declared, not inferred, and conformance checks that the claims
are honest: a provider that says it does not support cloning must *raise* when
asked to clone, not quietly substitute a default voice.
"""

from typing import Literal

from pydantic import BaseModel, Field

from gotiny.core.types import Language

Modality = Literal["tts", "stt", "llm"]

# Coarser is worse for a caller waiting on first audio.
_GRANULARITY = {"frame": 0, "sentence": 1, "utterance": 2}


class ProviderCaps(BaseModel):
    model_config = {"frozen": True}

    name: str = Field(description="Registry key, 'name@semver' — e.g. 'indicf5@0.3'")
    modality: Modality
    languages: frozenset[Language]
    sample_rates: frozenset[int]

    streaming: bool = Field(
        description="True only if audio is emitted before the full utterance is synthesised."
    )
    supports_cloning: bool = Field(
        default=False,
        description="Reference-conditioned synthesis. False for fixed-voice models (Kokoro).",
    )
    chunk_granularity: Literal["frame", "sentence", "utterance"] = "sentence"

    def supports(self, language: Language) -> bool:
        return language in self.languages

    @classmethod
    def fleet(cls, caps: "list[ProviderCaps]") -> "ProviderCaps":
        """One caps object describing what a *server* can collectively serve.

        A client holds this to answer "is it worth opening a socket for this
        request at all". It is not a description of any single model -- the
        server routes to a backend by voice_id, and only it knows which.

        It unions where a request could be served by *some* backend (languages,
        sample rates, cloning), and takes the worst case where the answer must
        hold for *whichever* backend answers (streaming, chunk granularity),
        because a client must not be promised streaming it might not get.

        Exists because ``discover()`` used to take ``backends[0]`` and call it
        the truth. With one backend that was indistinguishable from correct.
        The second backend made it a bug: half the fleet's languages vanished
        from the client's view depending on dict ordering.
        """
        if not caps:
            raise ValueError("fleet() needs at least one ProviderCaps")
        if len(caps) == 1:
            return caps[0]
        modality = caps[0].modality
        if any(c.modality != modality for c in caps):
            raise ValueError("cannot merge caps across modalities")
        coarsest = max((c.chunk_granularity for c in caps), key=_GRANULARITY.__getitem__)
        return cls(
            name="+".join(sorted(c.name for c in caps)),
            modality=modality,
            languages=frozenset().union(*(c.languages for c in caps)),
            sample_rates=frozenset().union(*(c.sample_rates for c in caps)),
            streaming=all(c.streaming for c in caps),
            supports_cloning=any(c.supports_cloning for c in caps),
            chunk_granularity=coarsest,
        )


class ProviderHealth(BaseModel):
    name: str
    healthy: bool
    detail: str | None = None
    loaded_ms: float | None = None
