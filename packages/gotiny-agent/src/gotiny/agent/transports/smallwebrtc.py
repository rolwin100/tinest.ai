"""Browser mic in, agent audio out, over WebRTC.

Phase 1 swaps this for SIP. Everything transport-specific is confined here so
that swap is days rather than a migration.
"""

from pipecat.transports.base_transport import TransportParams
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport


def build_transport(
    connection: SmallWebRTCConnection, in_rate: int, out_rate: int
) -> SmallWebRTCTransport:
    """Input and output run at different rates, deliberately.

    Silero VAD accepts only 16 kHz or 8 kHz and raises on anything else, and
    Whisper's native rate is 16 kHz -- so the capture side is 16 kHz and nothing
    resamples before recognition. Kokoro is native 24 kHz, so the playback side
    is 24 kHz and nothing resamples after synthesis. One rate for both would
    force a conversion onto one of the two hottest paths in the call.
    """
    return SmallWebRTCTransport(
        webrtc_connection=connection,
        params=TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            audio_in_sample_rate=in_rate,
            audio_out_sample_rate=out_rate,
            # The pipeline needs raw audio to reach our VADProcessor and STT.
            audio_in_passthrough=True,
        ),
    )
