"""One call, start to finish.

Hosted as an asyncio task inside the gateway process, not a separate process.
The warm-pool rationale went stale when the models moved into their own servers
that load weights at startup -- a bot now imports Pipecat and opens two HTTP
clients, so there is no cold model to hide. Crash isolation is the remaining
argument for processes, and that is a measurement away, not an assumption.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime

from pipecat.frames.frames import EndFrame
from pipecat.pipeline.runner import PipelineRunner
from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection

from gotiny.agent.persona import Persona
from gotiny.agent.pipeline import build_pipeline_task
from gotiny.core.logging import bind_call, get_logger

log = get_logger("gotiny.agent.bot")

EndReason = str  # completed | caller_hangup | agent_error | drained | rejected_capacity


@dataclass
class CallResult:
    call_id: str
    end_reason: EndReason = "completed"
    detail: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None

    @property
    def duration_s(self) -> float:
        end = self.ended_at or datetime.now(UTC)
        return (end - self.started_at).total_seconds()


async def run_call(
    call_id: str,
    persona: Persona,
    connection: SmallWebRTCConnection,
    stop: asyncio.Event | None = None,
) -> CallResult:
    """Run the pipeline until the caller leaves, we are drained, or it breaks.

    Always returns a CallResult -- never raises. An ``end_reason`` on every call
    is the difference between "we had 40 calls" and "we had 40 calls, 3 of which
    crashed", and it cannot be added retroactively.
    """
    bind_call(call_id, persona=persona.slug)
    result = CallResult(call_id=call_id)

    try:
        task, _aggregators = build_pipeline_task(persona, connection)
    except Exception as e:  # noqa: BLE001 - a failed build must still be recorded
        log.exception("pipeline_build_failed")
        result.end_reason, result.detail = "agent_error", f"{type(e).__name__}: {e}"
        result.ended_at = datetime.now(UTC)
        return result

    @connection.event_handler("closed")
    async def _on_closed(_conn: SmallWebRTCConnection) -> None:
        log.info("caller_hangup")
        if result.end_reason == "completed":
            result.end_reason = "caller_hangup"
        await task.queue_frame(EndFrame())

    # The gateway owns process lifecycle, so the per-call runner must not install
    # its own signal handlers -- otherwise every call fights over SIGTERM.
    runner = PipelineRunner(handle_sigint=False, handle_sigterm=False)

    drain_watcher = asyncio.create_task(_watch_drain(stop, task, result)) if stop else None
    try:
        await runner.run(task)
    except asyncio.CancelledError:
        result.end_reason = "drained"
        raise
    except Exception as e:  # noqa: BLE001
        log.exception("call_failed")
        result.end_reason, result.detail = "agent_error", f"{type(e).__name__}: {e}"
    finally:
        if drain_watcher:
            drain_watcher.cancel()
        # Always close the peer connection. aiortc holds ICE transports on their
        # own threads, so a connection left open leaks per call.
        try:
            await connection.disconnect()
        except Exception as e:  # noqa: BLE001 - teardown must not mask the result
            log.warning("connection_close_failed", error=f"{type(e).__name__}: {e}")
        result.ended_at = datetime.now(UTC)
        log.info(
            "call_ended",
            end_reason=result.end_reason,
            duration_s=round(result.duration_s, 1),
            detail=result.detail,
        )
    return result


async def _watch_drain(stop: asyncio.Event, task, result: CallResult) -> None:
    """A drain asks the call to finish; it does not kill it mid-sentence."""
    await stop.wait()
    log.info("drain_requested")
    result.end_reason = "drained"
    await task.queue_frame(EndFrame())
