"""Qwen3-TTS: bigger, slower, and expressive in a way Kokoro cannot be.

Why this exists alongside Kokoro rather than replacing it. Kokoro is 82M
parameters generating an utterance in one pass; this is 0.6B generating audio
token by token. That is roughly 7x the weights and a fundamentally slower
shape, so expect the TTS hop to go from a few hundred milliseconds to seconds
on a laptop. Measure it with `just say` before believing anything else.

What you get for that: ``instruct`` -- a natural-language description of *how*
to say the line ("warm and welcoming", "brisk and apologetic"). Kokoro reads
punctuation and nothing else; no amount of prompting gives it a tone. The flip
side is that the instruction is obeyed literally, pace included -- see _PACE.

**Except on the checkpoint this file defaults to.** ``qwen_tts`` silently sets
``instruct = None`` for the 0.6B CustomVoice model before generation ever
happens (see ``_model_supports_instruct`` below for the exact library check).
Every ``Speaker|instruct`` string in ``voices.yaml`` -- delivery, pace, "do not
laugh" -- is inert on ``DEFAULT_MODEL``. This backend logs a warning on load
and on first affected call so that is loud instead of silent; the 1.7B
CustomVoice checkpoint is the one that actually honours ``instruct``.

Honest caps: no Indic languages. Qwen3-TTS covers Chinese, English, Japanese,
Korean, German, French, Russian, Portuguese, Spanish and Italian. Hindi is not
among them, so this cannot serve the primary market -- it is an English-side
option and a Phase 2 Lane B candidate, not a replacement for IndicF5.

First live run confirmed 20 Sept 2026 (en-agent-01 / Ryan, on the 0.6B
checkpoint) -- which is how the instruct-drop above was found: an explicit
"do not laugh" in voices.yaml was still audibly ignored. Only that path has
been exercised; treat everything else here as still provisional.
"""

import asyncio
import os

import numpy as np

from gotiny.core.errors import ProviderError, ProviderUnavailable, UnsupportedLanguage
from gotiny.core.logging import get_logger
from gotiny.core.types import Language
from gotiny.providers.caps import ProviderCaps

log = get_logger("gotiny.tts.qwen3")

# Qwen3-TTS names languages in full words, not codes.
_LANG = {Language.ENGLISH_US: "English"}

# Confirmed 20 Sept 2026 by querying the loaded checkpoint directly
# (Qwen3TTSModel.get_supported_speakers() -- the roster is baked into the
# checkpoint's own config, qwen_tts does not hardcode it anywhere):
#
#   languages: auto, chinese, english, french, german, italian, japanese,
#              korean, portuguese, russian, spanish  (no Hindi -- see module
#              docstring on Indic coverage)
#   speakers:  aiden, dylan, eric, ono_anna, ryan, serena, sohee, uncle_fu,
#              vivian
#
# The name of a speaker does not predict which language(s) it is good at --
# "Ono_anna" reads as Japanese and is already in production as an English
# contact-centre voice (en-agent-03). So this is not "the English ones and
# the rest": every name below can be asked for `language="English"`, and the
# only way to know if it sounds right is to listen, same as voices.yaml's
# `grade` field exists for. Dylan/Eric/Serena/Sohee/Uncle_fu/Vivian are added
# here as *candidates* -- UNAUDITIONED. Run `just say voice="<Speaker>"` for
# each before wiring one into voices.yaml as a real product voice; update
# this comment (and that voice's `grade`) once you have.
_SPEAKERS = ("Ryan", "Aiden", "Ono_anna", "Dylan", "Eric", "Serena", "Sohee", "Uncle_fu", "Vivian")

DEFAULT_MODEL = "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"

# Qwen3-TTS has no numeric rate parameter -- ``instruct`` is the only pace
# control it has. So the wire's ``speed`` float is translated into words and
# appended to whatever style the voice already asks for. Coarse by nature: the
# model is being persuaded, not configured, so do not expect 1.15 to come out
# exactly 15% shorter. Kokoro takes the float directly and is exact.
_PACE = (
    (0.85, "Speak slowly and deliberately."),
    (0.95, "Speak a little slower than usual."),
    (1.05, ""),  # 1.0 -- say nothing, let the voice sit at its own pace
    (1.25, "Speak at a brisk conversational pace, without rushing."),
    (99.0, "Speak quickly."),
)


def _pace_instruction(speed: float) -> str:
    for threshold, phrase in _PACE:
        if speed < threshold:
            return phrase
    return ""


# Autoregressive decoding is unforgiving about dynamic range, and this is the
# lesson written down so it is not relearned: float16 tops out at 65504, and
# attention logits overflow it. The overflow becomes inf, softmax turns inf into
# nan, and torch.multinomial rejects the row with
#
#     probability tensor contains either `inf`, `nan` or element < 0
#
# bfloat16 has float32's exponent range with fewer mantissa bits, so it cannot
# overflow that way -- which is why it, not fp16, is the half precision every
# generative stack defaults to. An earlier version of this file picked fp16 on
# Metal for speed and traded away the property that keeps sampling valid.
#
# CPU gets fp32: half precision there is emulated, so it is slower *and* riskier.
_DTYPE_BY_DEVICE = {"cuda": "bfloat16", "mps": "bfloat16", "cpu": "float32"}


def _dtype_for(device: str, torch) -> object:  # noqa: ANN001 - torch typed at call site
    """Pick a generation-safe dtype, overridable when a box disagrees.

    ``GOTINY_QWEN_DTYPE=float32`` is the escape hatch: it is the slowest and the
    most memory-hungry option, and the one that always works. Reach for it if
    generation still produces nan on this hardware.
    """
    name = os.getenv("GOTINY_QWEN_DTYPE") or _DTYPE_BY_DEVICE[device.split(":")[0]]
    dtype = getattr(torch, name, None)
    if dtype is None:
        raise ProviderUnavailable(f"GOTINY_QWEN_DTYPE={name!r} is not a torch dtype")
    return dtype


def _device() -> str:
    """cuda on the GPU box, mps on the Mac, cpu as the floor."""
    try:
        import torch
    except ModuleNotFoundError:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda:0"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _model_supports_instruct(model: object) -> bool:  # noqa: ANN401 - qwen_tts type, not imported at module scope
    """Mirror qwen_tts's own gate so we can warn instead of losing `instruct` silently.

    ``qwen3_tts_model.py``'s ``generate_custom_voice`` does, verbatim::

        if self.model.tts_model_size in "0b6":  # for 0b6 model, instruct is not supported
            instruct = None

    -- a substring check against the literal string "0b6", which is how this
    library tags the 0.6B checkpoint's size internally (``self.model`` there is
    the wrapped HF model, reached the same way below). Replicated here,
    defensively: if a future qwen_tts release drops or renames the attribute,
    this returns True (assume instruct works) rather than raising a false
    alarm on every load.
    """
    size_tag = getattr(getattr(model, "model", None), "tts_model_size", None)
    if not isinstance(size_tag, str):
        return True
    return size_tag not in "0b6"


class Qwen3TTSBackend:
    # Corrected from the model's own return value on first synthesis: the
    # published docs are ambiguous about output rate, and guessing wrong would
    # silently pitch-shift every reply.
    native_sample_rate = 24_000

    def __init__(self, model_id: str | None = None) -> None:
        self._model = None
        self._device_used = "?"
        # Set for real once the checkpoint is loaded (see _model_supports_instruct).
        # Assumed True until then so a caps/log line printed before load doesn't
        # falsely claim the checkpoint has no instruct support.
        self._instruct_supported = True
        self._warned_instruct_dropped = False
        self._id = model_id or os.getenv("GOTINY_QWEN_TTS_MODEL", DEFAULT_MODEL)
        # No dot in the name: provider ids follow the registry's name@semver
        # shape, and "0.6b" would put a second dot in the version position.
        size = "1700m" if "1.7B" in self._id else "600m"
        self.caps = ProviderCaps(
            name=f"qwen3-tts-{size}@1.0",
            modality="tts",
            languages=frozenset(_LANG),
            sample_rates=frozenset({8_000, 16_000, 24_000}),
            streaming=False,
            supports_cloning=False,  # the Base variant clones; CustomVoice does not
            chunk_granularity="utterance",
        )

    async def load(self) -> None:
        try:
            import torch
            from qwen_tts import Qwen3TTSModel
        except ModuleNotFoundError as e:
            raise ProviderUnavailable(
                "qwen-tts not installed; run: uv sync --all-packages --extra qwen"
            ) from e

        device = _device()
        dtype = _dtype_for(device, torch)
        kwargs: dict = {"device_map": device, "dtype": dtype}
        # FlashAttention is CUDA-only; asking for it on mps or cpu fails at load.
        if device.startswith("cuda"):
            kwargs["attn_implementation"] = "flash_attention_2"

        self._model = await asyncio.to_thread(Qwen3TTSModel.from_pretrained, self._id, **kwargs)
        self._device_used = f"{device}/{dtype}"
        self._instruct_supported = _model_supports_instruct(self._model)
        log.info(
            "qwen3_tts_loaded",
            model=self._id,
            device=device,
            dtype=str(dtype),
            instruct_supported=self._instruct_supported,
        )
        if not self._instruct_supported:
            log.warning(
                "qwen3_tts_instruct_unsupported",
                model=self._id,
                detail=(
                    "qwen_tts sets instruct=None for this checkpoint's tts_model_size "
                    "before generation (see _model_supports_instruct). Every "
                    "'Speaker|instruct' string in voices.yaml for this backend -- "
                    "delivery, pace, 'do not laugh' -- is silently discarded. Set "
                    "GOTINY_QWEN_TTS_MODEL to the 1.7B CustomVoice checkpoint for "
                    "instruct to actually take effect."
                ),
            )

    async def synth(self, segment: str, *, voice: str, language: Language, speed: float) -> bytes:
        if self._model is None:
            raise ProviderUnavailable("qwen3-tts backend not loaded")
        lang = _LANG.get(language)
        if lang is None:
            raise UnsupportedLanguage(f"qwen3-tts has no voice for {language}")

        # voices.yaml carries "Ryan" or "Ryan|warm and welcoming" -- the part
        # after the pipe is the style instruction, which is the whole reason to
        # pay this model's latency. Mind the adjectives: they are obeyed, and an
        # early draft of en-warm-01 said "unhurried", which the model duly was.
        speaker, _, instruct = voice.partition("|")
        if speaker not in _SPEAKERS:
            raise UnsupportedLanguage(
                f"qwen3-tts English speakers are {_SPEAKERS}, got {speaker!r}"
            )

        pace = _pace_instruction(speed)
        instruct = ". ".join(part for part in (instruct.rstrip(". "), pace) if part) or None

        if instruct is not None and not self._instruct_supported and not self._warned_instruct_dropped:
            self._warned_instruct_dropped = True
            log.warning(
                "qwen3_tts_instruct_dropped",
                voice=voice,
                model=self._id,
                detail="this call's instruct is discarded by qwen_tts on this checkpoint -- see qwen3_tts_instruct_unsupported logged at load",
            )

        def _run() -> tuple[np.ndarray, int]:
            wavs, sr = self._model.generate_custom_voice(  # type: ignore[union-attr]
                text=segment,
                language=lang,
                speaker=speaker,
                instruct=instruct,
            )
            return np.asarray(wavs[0], dtype=np.float32), int(sr)

        try:
            audio, sr = await asyncio.to_thread(_run)
        except RuntimeError as e:
            # Torch raises this from multinomial when the logits went non-finite.
            # Almost always dtype range, occasionally a bad instruct string.
            if "probability tensor" in str(e) or "nan" in str(e).lower():
                raise ProviderError(
                    f"qwen3-tts produced non-finite logits on {self._device_used}. "
                    "This is a numeric-range failure, not a bad request: retry with "
                    "GOTINY_QWEN_DTYPE=float32 (slower, always works). "
                    f"Original: {e}"
                ) from e
            raise
        # Trust the model over the docs about its own output rate.
        if sr != self.native_sample_rate:
            log.info("qwen3_tts_rate", reported=sr, assumed=self.native_sample_rate)
            self.native_sample_rate = sr
        return (np.clip(audio, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()
