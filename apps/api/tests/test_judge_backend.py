"""Remote judge dispatch: configuration guardrails and failure handling.

The happy path needs real GCP credentials, but everything that can go wrong
around it is testable offline, and those are the paths that decide whether a
user sees a clean error or a 500.
"""

import time

import pytest

from app.config import Settings
from app.services import judge_backend


@pytest.fixture
def settings_snapshot():
    """Restores global settings after a test mutates them."""
    from app.config import settings

    original = (
        settings.judge_url,
        settings.google_application_credentials,
        settings.judge_timeout_sec,
    )
    yield settings
    (
        settings.judge_url,
        settings.google_application_credentials,
        settings.judge_timeout_sec,
    ) = original


def _base_env() -> dict:
    return {
        "secret_key": "a-sufficiently-long-test-secret-key-for-validation",
        "environment": "production",
    }


def test_judge_url_without_credentials_refuses_to_start():
    """A remote judge with no way to authenticate is a broken deploy, so it
    must fail at startup rather than on the first submission."""
    with pytest.raises(Exception) as exc:
        Settings(
            **_base_env(),
            judge_url="https://judge.example.run.app",
            google_application_credentials="",
        )
    assert "GOOGLE_APPLICATION_CREDENTIALS" in str(exc.value)


def test_judge_url_with_credentials_is_accepted():
    cfg = Settings(
        **_base_env(),
        judge_url="https://judge.example.run.app",
        google_application_credentials="/run/secrets/judge-sa.json",
    )
    assert cfg.judge_url == "https://judge.example.run.app"


def test_local_sandbox_is_the_default():
    cfg = Settings(**_base_env())
    assert cfg.judge_url == ""


@pytest.mark.asyncio
async def test_unmintable_token_returns_clean_re(settings_snapshot, monkeypatch):
    """If the identity cannot be minted, the submission must fail with an
    honest, gradeable error instead of raising through the endpoint."""
    settings_snapshot.judge_url = "https://judge.example.run.app"
    settings_snapshot.google_application_credentials = "/nonexistent/key.json"

    # Force a cache miss so the refresh path actually runs.
    judge_backend._cached_token = None

    result = await judge_backend.execute(
        language="python",
        code="def solve(): pass",
        function_name="solve",
        test_cases=[{"input": [], "expected": None}],
    )

    assert result.verdict == "RE"
    assert result.test_results == []
    # The message must say nothing was graded, so the UI cannot imply a score.
    assert "nothing was graded" in result.compile_output.lower()


@pytest.mark.asyncio
async def test_unreachable_service_returns_clean_re(settings_snapshot, monkeypatch):
    """A network failure to the judge must not surface as a 500."""
    settings_snapshot.judge_url = "http://127.0.0.1:9"  # nothing listens here
    settings_snapshot.judge_timeout_sec = 2.0

    async def _fake_token() -> str:
        return "fake-identity-token"

    monkeypatch.setattr(judge_backend, "_mint_identity_token", _fake_token)

    result = await judge_backend.execute(
        language="python",
        code="def solve(): pass",
        function_name="solve",
        test_cases=[{"input": [], "expected": None}],
    )

    assert result.verdict == "RE"
    assert "could not be reached" in result.compile_output.lower()


def _write_service_account_file(tmp_path):
    """A structurally valid service-account file backed by a throwaway key.

    Real enough that google-auth parses it and signs a JWT, so the code reaches
    the HTTP layer instead of stopping at a parse error. `token_uri` points at a
    dead port so the request fails fast and locally.
    """
    import json

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    path = tmp_path / "judge-sa.json"
    path.write_text(
        json.dumps(
            {
                "type": "service_account",
                "project_id": "merit-test",
                "private_key_id": "test",
                "private_key": pem,
                "client_email": "judge@merit-test.iam.gserviceaccount.com",
                "client_id": "1",
                "token_uri": "http://127.0.0.1:9/token",
            }
        )
    )
    return str(path)


def test_minting_reaches_the_network_instead_of_failing_to_import(tmp_path):
    """Regression guard for a shipped break.

    google-auth imports its HTTP transport lazily, so `google-auth` without the
    `[requests]` extra let the API boot, pass this entire suite, and then fail
    every submission in production with "the code runner is temporarily
    unavailable" — requests appeared nowhere in the traceback until it was
    already in front of a user.

    The two tests above cannot catch that class of bug: one stubs the minting
    function outright, the other points at a nonexistent key path. Both
    short-circuit before the transport is ever imported. This one drives the
    real function and asserts the failure is the unreachable token endpoint
    rather than a missing module.
    """
    credentials_path = _write_service_account_file(tmp_path)

    with pytest.raises(Exception) as exc:
        judge_backend._refresh_identity_token(
            credentials_path, "https://judge.example.run.app", time.time()
        )

    assert not isinstance(exc.value, (ImportError, ModuleNotFoundError)), (
        "the token-minting path is missing a dependency; in production this "
        f"fails every submission. Got: {exc.value!r}"
    )
