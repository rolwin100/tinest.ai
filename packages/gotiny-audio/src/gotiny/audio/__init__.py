"""PCM helpers.

Promoted out of ``services/tts/util/audio.py`` the moment ``services/stt`` needed
the same resampler. Both directions of the pipeline convert between the rate a
model wants and the rate the call is running at, so this is shared ground -- and
week 3's corpus tooling will want exactly these functions too.
"""

from gotiny.audio.pcm import duration_ms, float32_to_pcm, pcm_to_float32, resample_pcm

__all__ = ["duration_ms", "float32_to_pcm", "pcm_to_float32", "resample_pcm"]
