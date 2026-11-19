"""POST /v1/stt -- raw PCM body, request metadata in a header.

Why not multipart or JSON+base64: audio is the payload, and base64 costs 33%
more bytes plus an encode/decode on the hot path. The header carries the small
typed part; the body is bytes, unmodified.
"""

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import ValidationError

from gotiny.core.errors import ProviderUnavailable, UnsupportedLanguage
from gotiny.providers.wire import WIRE_VERSION, STTRequest, STTResponse
from gotiny.stt.services.transcription import transcribe

router = APIRouter()

REQUEST_HEADER = "x-gotiny-request"


@router.post(f"/{WIRE_VERSION}/stt", response_model=STTResponse)
async def stt(
    request: Request,
    x_gotiny_request: str = Header(..., alias=REQUEST_HEADER),
) -> STTResponse:
    try:
        req = STTRequest.model_validate_json(x_gotiny_request)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=f"bad {REQUEST_HEADER}: {e}") from e

    pcm = await request.body()
    if not pcm:
        raise HTTPException(status_code=400, detail="empty audio body")
    if len(pcm) % 2:
        raise HTTPException(status_code=400, detail="body is not 16-bit PCM (odd length)")

    try:
        return await transcribe(pcm, req, request.app.state.router)
    except UnsupportedLanguage as e:
        # 422, not 503: retrying will never help. Mirrors the TTSError taxonomy.
        raise HTTPException(status_code=422, detail=str(e)) from e
    except ProviderUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
