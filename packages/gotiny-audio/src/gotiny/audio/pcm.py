"""Raw PCM s16le, mono. The only audio representation that crosses our wire.

8 kHz is not a degraded mode we tolerate -- it is the target condition for most
traffic. Naive decimation aliases badly at 24k->8k, so resampling goes through
soxr rather than array slicing.
"""

import numpy as np
import soxr


def pcm_to_float32(pcm: bytes) -> np.ndarray:
    """s16le bytes -> float32 in [-1, 1], which is what every model wants."""
    return np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0


def float32_to_pcm(samples: np.ndarray) -> bytes:
    return (np.clip(samples, -1.0, 1.0) * 32767.0).astype("<i2").tobytes()


def resample_pcm(pcm: bytes, src_rate: int, dst_rate: int) -> bytes:
    if src_rate == dst_rate or not pcm:
        return pcm
    return float32_to_pcm(soxr.resample(pcm_to_float32(pcm), src_rate, dst_rate))


def duration_ms(pcm: bytes, sample_rate: int) -> float:
    return (len(pcm) / 2) / sample_rate * 1_000
