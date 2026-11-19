"""The dev playground page, served at /.

A single static file on purpose. The Next.js console arrives in Phase 1, when
there is a call log, a transcript viewer and an agent config editor to build --
UI worth a build step. Today the only job is "let me talk to it and see which
hop broke", and a page with no toolchain does that today rather than after an
npm install.

Mounted only if the file exists, so the gateway still runs headless.
"""

from fastapi import APIRouter, Response
from fastapi.responses import FileResponse, JSONResponse

from gotiny.core.paths import find_repo_root

router = APIRouter()

_ROOT = find_repo_root()
PAGE = _ROOT / "apps" / "console" / "index.html" if _ROOT else None


@router.get("/", include_in_schema=False)
async def playground() -> Response:
    # Annotated as Response, not a union of response classes: FastAPI reads the
    # return annotation as a response_model and rejects the union.
    if PAGE is None or not PAGE.exists():
        return JSONResponse({"detail": f"playground page not found at {PAGE}"}, status_code=404)
    # No caching: this file gets edited constantly during turn-taking tuning.
    return FileResponse(PAGE, headers={"cache-control": "no-store"})
