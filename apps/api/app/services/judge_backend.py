"""Judge backend selection.

Two execution paths, one contract:

- **Remote** — when `JUDGE_URL` is set, submissions are sent to the Cloud Run
  judge service, which runs them in its own isolated container with no access
  to this API's database, secrets, or filesystem.
- **Local** — otherwise, the in-process sandbox (`services/judge.py`) runs them
  the way it always has. This keeps local development and the test suite
  working with no cloud credentials and no network.

The return type is identical either way, so routers do not care which path ran.
"""

import asyncio
import logging
import time
from typing import Any

import httpx

from app.config import settings
from app.services.judge import JudgeResult, execute_code

logger = logging.getLogger(__name__)

# Identity tokens are valid for an hour; refresh a little early so an
# in-flight request never presents a token that expires mid-call.
_TOKEN_REFRESH_SKEW_SEC = 300
_cached_token: tuple[str, float] | None = None
_token_lock = asyncio.Lock()


async def _mint_identity_token() -> str | None:
    """Mints a Google-signed ID token for the judge service, with caching.

    Imported lazily so the API does not require google-auth unless a remote
    judge is actually configured.
    """
    global _cached_token

    now = time.time()
    if _cached_token and _cached_token[1] - _TOKEN_REFRESH_SKEW_SEC > now:
        return _cached_token[0]

    async with _token_lock:
        # Another coroutine may have refreshed while we waited for the lock.
        now = time.time()
        if _cached_token and _cached_token[1] - _TOKEN_REFRESH_SKEW_SEC > now:
            return _cached_token[0]

        def _refresh() -> tuple[str, float]:
            from google.auth.transport.requests import Request
            from google.oauth2 import service_account

            credentials = service_account.IDTokenCredentials.from_service_account_file(
                settings.google_application_credentials,
                target_audience=settings.judge_url,
            )
            credentials.refresh(Request())
            # google-auth exposes expiry as datetime; convert to epoch seconds.
            expires_at = credentials.expiry.timestamp() if credentials.expiry else now + 3600
            return credentials.token, expires_at

        try:
            # Blocking network + file IO, so keep it off the event loop.
            token, expires_at = await asyncio.to_thread(_refresh)
        except Exception:
            logger.exception("Could not mint an identity token for the judge service")
            return None

        _cached_token = (token, expires_at)
        return token


async def execute(
    language: str,
    code: str,
    function_name: str,
    test_cases: list[dict[str, Any]],
    time_limit_ms: int = 2000,
) -> JudgeResult:
    """Runs a submission on the configured backend."""
    if not settings.judge_url:
        return await execute_code(
            language=language,
            code=code,
            function_name=function_name,
            test_cases=test_cases,
            time_limit_ms=time_limit_ms,
        )

    token = await _mint_identity_token()
    if token is None:
        return JudgeResult(
            verdict="RE",
            runtime_ms=0,
            test_results=[],
            compile_output=(
                "The code runner is temporarily unavailable. Nothing was graded."
            ),
        )

    payload = {
        "language": language,
        "code": code,
        "function_name": function_name,
        "test_cases": test_cases,
        "time_limit_ms": time_limit_ms,
    }

    try:
        # Cloud Run cold starts on a heavy image can take several seconds, so
        # this timeout is deliberately far above the judge's own time limit.
        async with httpx.AsyncClient(timeout=settings.judge_timeout_sec) as client:
            resp = await client.post(
                f"{settings.judge_url.rstrip('/')}/run",
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.HTTPError as err:
        logger.warning("Judge service unreachable: %s", err)
        return JudgeResult(
            verdict="RE",
            runtime_ms=0,
            test_results=[],
            compile_output=(
                "The code runner could not be reached. Nothing was graded, "
                "so no attempt was recorded."
            ),
        )

    if resp.status_code == 401:
        # A stale or wrong-audience token is an operator problem, not the
        # submitter's. Surface it as an infrastructure failure.
        logger.error("Judge service rejected our identity token")
        return JudgeResult(
            verdict="RE",
            runtime_ms=0,
            test_results=[],
            compile_output="The code runner rejected this request. Nothing was graded.",
        )

    if resp.status_code >= 400:
        logger.warning("Judge service error %s: %s", resp.status_code, resp.text[:200])
        return JudgeResult(
            verdict="RE",
            runtime_ms=0,
            test_results=[],
            compile_output="The code runner failed to process this submission.",
        )

    data = resp.json()
    return JudgeResult(
        verdict=data.get("verdict", "RE"),
        runtime_ms=data.get("runtime_ms", 0.0),
        test_results=data.get("test_results", []),
        compile_output=data.get("compile_output", ""),
    )
