"""Rate limiting: the bucket maths and a real 429 from the feedback endpoint.

There was no test for a 429 anywhere in the suite, so the limiter could have been
broken (or silently never applied) without anyone noticing.
"""

import pytest
from fastapi import HTTPException

from app.services.rate_limit import SlidingWindowLimiter, client_key


class _Req:
    class _Client:
        host = "203.0.113.7"

    client = _Client()


def test_allows_up_to_the_budget_then_rejects():
    limiter = SlidingWindowLimiter(
        max_hits=3, window_sec=60, code="TEST_LIMIT", message="slow down"
    )
    for _ in range(3):
        limiter.check("k")

    with pytest.raises(HTTPException) as caught:
        limiter.check("k")
    assert caught.value.status_code == 429
    assert caught.value.detail["code"] == "TEST_LIMIT"
    # Retry-After must be a positive number of seconds.
    assert int(caught.value.headers["Retry-After"]) >= 1


def test_keys_are_independent():
    limiter = SlidingWindowLimiter(
        max_hits=1, window_sec=60, code="TEST_LIMIT", message="slow down"
    )
    limiter.check("a")
    limiter.check("b")  # a different key still has budget
    with pytest.raises(HTTPException):
        limiter.check("a")


def test_reset_clears_buckets():
    limiter = SlidingWindowLimiter(
        max_hits=1, window_sec=60, code="TEST_LIMIT", message="slow down"
    )
    limiter.check("k")
    limiter.reset()
    limiter.check("k")  # must not raise


def test_stale_buckets_are_dropped_and_the_sweep_trigger_doubles():
    """Dead keys must not accumulate, and sweeping must not be O(n) per request.

    The trigger doubles each time it fires, so the scan is amortised to O(1) per
    insert instead of running on every request once the dict is over the
    threshold.
    """
    import time

    import app.services.rate_limit as module

    limiter = SlidingWindowLimiter(
        max_hits=5, window_sec=0.05, code="TEST_LIMIT", message="slow down"
    )
    assert limiter._sweep_at == module._SWEEP_THRESHOLD

    for i in range(module._SWEEP_THRESHOLD):
        limiter.check(f"ip-{i}")

    # Crossing the threshold fires a sweep and doubles the next trigger.
    limiter.check("crossing")
    assert limiter._sweep_at > module._SWEEP_THRESHOLD

    # Everything is now outside the window, so an explicit sweep empties it.
    time.sleep(0.06)
    limiter._sweep(time.monotonic())
    assert limiter._hits == {}, f"expected an empty dict, got {len(limiter._hits)} keys"

    # And reset restores the trigger for the next test.
    limiter.reset()
    assert limiter._sweep_at == module._SWEEP_THRESHOLD


def test_client_key_falls_back_when_there_is_no_client():
    class _NoClient:
        client = None

    assert client_key(_NoClient()) == "unknown"
    assert client_key(_Req()) == "203.0.113.7"


def test_feedback_endpoint_returns_429_after_its_budget(client):
    """The endpoint actually applies the limiter.

    Uses a fresh client IP per test (the limiter is reset by the conftest
    fixture) and the real budget of 10/hour.
    """
    payload = {"category": "bug", "title": "Bug report", "description": "Something broke."}

    accepted = 0
    limited = None
    for _ in range(12):
        response = client.post("/api/v1/feedback", json=payload)
        if response.status_code == 201:
            accepted += 1
        elif response.status_code == 429:
            limited = response
            break
        else:  # pragma: no cover - surfaces a different failure clearly
            pytest.fail(f"unexpected status {response.status_code}: {response.text}")

    assert accepted == 10, f"budget should be 10, got {accepted}"
    assert limited is not None
    assert limited.json()["detail"]["code"] == "FEEDBACK_RATE_LIMIT"
