"""Merit judge service — executes untrusted submissions in an isolated container.

This is the Cloud Run workload. It is deliberately tiny: it holds no database,
no secrets, and no user data. It receives code and test cases, runs them inside
the hardened sandbox, and returns the verdict.

The sandbox itself (`sandbox.py`) is copied verbatim from
`apps/api/app/services/judge.py` at build time, so local development and this
service always execute code the same way.

Authentication is handled by the platform: the service is deployed with
`--no-allow-unauthenticated`, so Cloud Run rejects any request that does not
carry a valid Google-issued identity token before it ever reaches this process.
There is no application-level secret to leak here.
"""

import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from sandbox import execute_code

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("merit.judge")

# Mirrors the API's own limits so a request that could never pass validation
# still fails fast here rather than spawning a process.
MAX_CODE_BYTES = 64 * 1024
SUPPORTED_LANGUAGES = {"python", "javascript"}

app = FastAPI(
    title="Merit Judge",
    version="1.0.0",
    # No interactive docs on a service that runs untrusted code.
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


class RunRequest(BaseModel):
    language: str = Field(..., description="python | javascript")
    code: str
    function_name: str
    test_cases: list[dict[str, Any]]
    time_limit_ms: int = 2000


class RunResponse(BaseModel):
    verdict: str
    runtime_ms: float
    test_results: list[dict[str, Any]]
    compile_output: str = ""


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness/startup probe. Cheap enough to answer during a cold start."""
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
async def run(req: RunRequest) -> RunResponse:
    if req.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported language {req.language!r}",
        )

    if len(req.code.encode("utf-8")) > MAX_CODE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Code exceeds the maximum size",
        )

    result = await execute_code(
        language=req.language,
        code=req.code,
        function_name=req.function_name,
        test_cases=req.test_cases,
        time_limit_ms=req.time_limit_ms,
    )

    # Log the shape of the run, never the submission itself.
    logger.info(
        "judge run language=%s verdict=%s tests=%d runtime_ms=%.1f",
        req.language,
        result.verdict,
        len(result.test_results),
        result.runtime_ms,
    )

    return RunResponse(
        verdict=result.verdict,
        runtime_ms=result.runtime_ms,
        test_results=result.test_results,
        compile_output=result.compile_output,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8080")),
    )
