"""Sentence segmentation -- and why it lives in the server.

Measured, not assumed: ``kokoro_onnx.create_stream`` returns **one chunk for the
entire input string**. It does not split on sentences. So a four-sentence reply
has a time-to-first-byte equal to the full synthesis time of all four -- which
blows the latency budget on exactly the replies that matter. Measured here:
segmenting cut Hindi TTFB from 4054 ms to 872 ms.

IndicF5 has the same shape (flow-matching, whole utterance at once), and so will
most reference-conditioned models. Putting segmentation in each backend would
mean writing it repeatedly and inconsistently.

So the server segments and calls the backend once per sentence. Every backend
then gets sentence-level streaming for free, and cancellation ("drop the
remaining sentences", ADR 0004) becomes uniformly implementable -- you simply
stop before synthesising the next one.
"""

import re

# Terminators include the Devanagari danda (।) and double danda (॥). Splitting
# Hindi on "." alone silently produces one giant segment.
# Fixed-width: Python lookbehind rejects a quantifier here.
_TERMINATORS = r"[.!?।॥]"
_SPLIT = re.compile(rf"(?<={_TERMINATORS})[\s]+")

# Guard: an unpunctuated monologue would otherwise be one enormous segment.
MAX_SEGMENT_CHARS = 240


def split_sentences(text: str, max_chars: int = MAX_SEGMENT_CHARS) -> list[str]:
    """Split into synthesis segments.

    Deliberately simple: no abbreviation handling ("Dr." splits). For a voice
    agent that is an acceptable trade -- an over-eager split costs a small prosody
    seam, while an under-eager one costs seconds of latency.
    """
    text = text.strip()
    if not text:
        return []

    segments: list[str] = []
    for part in _SPLIT.split(text):
        part = part.strip()
        if not part:
            continue
        if len(part) <= max_chars:
            segments.append(part)
            continue
        segments.extend(_soft_wrap(part, max_chars))
    return segments


def _soft_wrap(part: str, max_chars: int) -> list[str]:
    """Long and unpunctuated: fall back to clause boundaries, then a hard wrap."""
    out: list[str] = []
    buf = ""
    for piece in re.split(r"(?<=[,;:—])\s+", part):
        candidate = f"{buf} {piece}".strip()
        if len(candidate) <= max_chars:
            buf = candidate
            continue
        if buf:
            out.append(buf)
        while len(piece) > max_chars:
            out.append(piece[:max_chars])
            piece = piece[max_chars:]
        buf = piece
    if buf:
        out.append(buf)
    return out

