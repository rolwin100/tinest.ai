"""Deprecated shim -- these live in ``packages/gotiny-audio`` now.

``services/stt`` needed the same resampler, so rather than copy it the functions
were promoted to a shared package. This file exists only so nothing breaks
mid-refactor; delete it and import from ``gotiny.audio`` directly.
"""

from gotiny.audio import duration_ms, resample_pcm

__all__ = ["duration_ms", "resample_pcm"]
