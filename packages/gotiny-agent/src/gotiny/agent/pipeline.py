"""Assemble one call's pipeline from a persona.

Order matters and is not arbitrary:

    transport.input      raw mic audio
    VADProcessor         speech boundaries -- must precede STT, which is a
                         SegmentedSTTService and triggers on VAD events
    stt                  audio -> text
    context.user()       text into the conversation history
    llm                  history -> reply, or a tool call
    tts                  text -> audio, sentence by sentence
    transport.output     audio to the caller
    context.assistant()  what we said, back into history

Note what is NOT here: any model library. The pipeline imports only
``gotiny.providers``, which is what makes swapping in our own weights in Phase 2
a config change. If this file needs editing to ship a custom model, the seam
failed.
"""

from pipecat.frames.frames import TTSSpeakFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection

from gotiny.agent.persona import Persona
from gotiny.agent.tools import resolve as resolve_tools
from gotiny.agent.transports.smallwebrtc import build_transport
from gotiny.agent.turn.policy import build_vad
from gotiny.core.logging import get_logger
from gotiny.core.settings import settings
from gotiny.providers.llm.openai_compat import build_llm
from gotiny.providers.stt.http import HTTPSTTBackend
from gotiny.providers.stt.pipecat_bridge import GotinySTTService
from gotiny.providers.tts.http import HTTPTTSBackend
from gotiny.providers.tts.pipecat_bridge import GotinyTTSService

log = get_logger("gotiny.agent.pipeline")

# Capture at 16 kHz: Silero VAD accepts only 16000 or 8000, and Whisper's native
# rate is 16 kHz, so nothing resamples before recognition.
IN_RATE = 16_000
# Play out at 24 kHz: Kokoro's native rate, so nothing resamples after synthesis.
OUT_RATE = 24_000


def build_pipeline_task(
    persona: Persona, connection: SmallWebRTCConnection
) -> tuple[PipelineTask, LLMContextAggregatorPair]:
    """Wire one call. Raises ProviderUnavailable if a model server is down."""
    transport = build_transport(connection, IN_RATE, OUT_RATE)

    # Capabilities are read from the servers, never hardcoded here.
    tts_backend = HTTPTTSBackend.discover(settings.tts_url)
    stt_backend = HTTPSTTBackend.discover(settings.stt_url)

    stt = GotinySTTService(backend=stt_backend, language=persona.language, sample_rate=IN_RATE)
    tts = GotinyTTSService(
        backend=tts_backend,
        voice_id=persona.voice_id,
        language=persona.language,
        sample_rate=OUT_RATE,
        speed=persona.speed,
    )

    llm = build_llm()
    schemas = []
    for schema, handler in resolve_tools(persona.tools):
        llm.register_function(schema.name, handler)
        schemas.append(schema)

    context = LLMContext(
        messages=[{"role": "system", "content": persona.system_message()}],
        tools=schemas or None,
    )
    aggregators = LLMContextAggregatorPair(context)

    pipeline = Pipeline(
        [
            transport.input(),
            build_vad(persona.turn),
            stt,
            aggregators.user(),
            llm,
            tts,
            transport.output(),
            aggregators.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            audio_in_sample_rate=IN_RATE,
            audio_out_sample_rate=OUT_RATE,
            # These are the spans week 2's `turn` table records. On by default so
            # nobody has to remember to switch instrumentation on.
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )
    @transport.event_handler("on_client_connected")
    async def _greet(_transport, _client) -> None:
        """Speak the opening the moment the caller connects.

        Straight to TTS, bypassing the LLM: the disclosure is a legal statement
        and the greeting is fixed, so neither should depend on a small model
        choosing to comply. It also means the caller hears something within a few
        hundred milliseconds instead of waiting for a first inference.
        """
        await task.queue_frames([TTSSpeakFrame(text=persona.opening())])

    log.info(
        "pipeline_built",
        persona=persona.slug,
        language=persona.language,
        voice=persona.voice_id,
        speed=persona.speed,
        tts=tts_backend.caps.name,
        stt=stt_backend.caps.name,
        llm=settings.llm_model,
        tools=persona.tools,
        stop_secs=persona.turn.stop_secs,
    )
    return task, aggregators
