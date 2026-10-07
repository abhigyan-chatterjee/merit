"""Judge backend selection.

Two execution paths, one contract:

- **Remote** — when a judge URL is set, submissions are sent to the Cloud Run
  judge service, which runs them in its own isolated container with no access
  to this API's database, secrets, or filesystem. Java and C++ go to a second
  service carrying the compile toolchain, so the interpreted languages keep a
  short cold start.
- **Local** — otherwise, the in-process sandbox (`services/judge.py`) runs them
  the way it always has. This keeps local development and the test suite
  working with no cloud credentials and no network.

The return type is identical either way, so routers do not care which path ran.
"""

import asyncio
import calendar
import logging
import time
from typing import Any

import httpx

from app.config import settings
from app.services.judge import JudgeResult, execute_code

logger = logging.getLogger(__name__)

# Languages that must be compiled before they run, and therefore need the
# toolchain image rather than the light one.
_COMPILED_LANGUAGES = frozenset({"java", "cpp"})

# Identity tokens are valid for an hour; refresh a little early so an
# in-flight request never presents a token that expires mid-call.
_TOKEN_REFRESH_SKEW_SEC = 300
# Keyed by audience: each judge service is a distinct token audience, so one
# cached token cannot be presented to the other.
_cached_tokens: dict[str, tuple[str, float]] = {}
_token_lock = asyncio.Lock()


def _judge_target_for(language: str) -> str:
    """Which judge service runs this language, or "" for the local sandbox.

    Either service can run any language — both images carry the same sandbox —
    so a deployment that configures only one URL still works: the preferred
    service is tried first and the other is the fallback.
    """
    light, heavy = settings.judge_url, settings.judge_heavy_url
    if language in _COMPILED_LANGUAGES:
        return heavy or light
    return light or heavy


def _expiry_epoch(expiry: Any, fallback_now: float) -> float:
    """Converts a google-auth expiry to epoch seconds, safely.

    google-auth returns a naive UTC datetime. Calling `.timestamp()` on a naive
    value reinterprets it as *local* time, so on a non-UTC host the cached
    expiry would be wrong by the UTC offset and the token could be used after
    it had already expired.
    """
    if expiry is None:
        return fallback_now + 3600
    if expiry.tzinfo is None:
        return float(calendar.timegm(expiry.utctimetuple()))
    return float(expiry.timestamp())


def _refresh_identity_token(
    credentials_path: str, audience: str, now: float
) -> tuple[str, float]:
    """Blocking token mint. Module-level, not a closure, so a test can drive it.

    google-auth imports its HTTP transport lazily at call time. That means a
    missing transport dependency is invisible at startup and only appears here —
    a fact that has already caused one production outage, hence the test that
    calls this directly rather than trusting the surrounding stub coverage.
    """
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account

    credentials = service_account.IDTokenCredentials.from_service_account_file(
        credentials_path,
        target_audience=audience,
    )
    credentials.refresh(Request())
    return credentials.token, _expiry_epoch(credentials.expiry, now)


async def _mint_identity_token(audience: str) -> str | None:
    """Mints a Google-signed ID token for one judge service, with caching.

    Cached because the token is valid for an hour: minting per submission would
    add a round trip to Google on the hot path. The google-auth import is
    function-local so that importing this module never requires the library,
    although it is a declared dependency of the API.
    """
    now = time.time()
    cached = _cached_tokens.get(audience)
    if cached and cached[1] - _TOKEN_REFRESH_SKEW_SEC > now:
        return cached[0]

    async with _token_lock:
        # Another coroutine may have refreshed while we waited for the lock.
        now = time.time()
        cached = _cached_tokens.get(audience)
        if cached and cached[1] - _TOKEN_REFRESH_SKEW_SEC > now:
            return cached[0]

        try:
            # Blocking network + file IO, so keep it off the event loop.
            token, expires_at = await asyncio.to_thread(
                _refresh_identity_token,
                settings.google_application_credentials,
                audience,
                now,
            )
        except Exception:
            logger.exception("Could not mint an identity token for %s", audience)
            return None

        _cached_tokens[audience] = (token, expires_at)
        return token


async def execute(
    language: str,
    code: str,
    function_name: str,
    test_cases: list[dict[str, Any]],
    time_limit_ms: int = 2000,
    signature: dict[str, Any] | None = None,
) -> JudgeResult:
    """Runs a submission on the configured backend.

    `signature` carries the problem's parameter and return types. Interpreted
    languages ignore it; Java and C++ need it to generate typed source.
    """
    target = _judge_target_for(language)
    if not target:
        return await execute_code(
            language=language,
            code=code,
            function_name=function_name,
            test_cases=test_cases,
            time_limit_ms=time_limit_ms,
            signature=signature,
        )

    token = await _mint_identity_token(target)
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
        "signature": signature,
    }

    try:
        # Cloud Run cold starts on a heavy image can take several seconds, so
        # this timeout is deliberately far above the judge's own time limit.
        async with httpx.AsyncClient(timeout=settings.judge_timeout_sec) as client:
            resp = await client.post(
                f"{target.rstrip('/')}/run",
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
