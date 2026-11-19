"""End-of-turn detection.

In Pipecat 1.7 VAD is a **pipeline processor**, not a transport parameter --
``TransportParams`` no longer carries ``vad_analyzer``. Most tutorials still show
the old shape, so this module exists partly to hold that fact in one place.

Why it gets its own module for ~20 lines: this is the largest single line in the
latency budget (300 ms of the 800 ms cloud target) and it is *tuning*, not code.
Everything that can be turned lives here and in the persona.
"""

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.processors.audio.vad_processor import VADProcessor

from gotiny.agent.persona import TurnConfig


def build_vad(turn: TurnConfig) -> VADProcessor:
    """Silero VAD as a pipeline processor.

    ``stop_secs`` is the knob that matters: it is dead time added to every single
    reply. Pipecat's default is 0.2 s, which interrupts real speakers mid-thought
    on a phone line; our persona default is 0.6 s. Semantic turn detection is the
    week-2 improvement over this.

    Note Silero accepts only 16 kHz or 8 kHz audio and raises on anything else --
    which is why the transport captures at 16 kHz. See ``pipeline.IN_RATE``.
    """
    return VADProcessor(
        vad_analyzer=SileroVADAnalyzer(
            params=VADParams(
                confidence=turn.confidence,
                start_secs=turn.start_secs,
                stop_secs=turn.stop_secs,
                min_volume=turn.min_volume,
            )
        )
    )
