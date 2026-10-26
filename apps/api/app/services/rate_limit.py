"""A small in-process sliding-window rate limiter.

Deliberately not a dependency: `slowapi` would pull in Redis or a store this
deployment does not run, and the API is a single uvicorn worker on a 1 vCPU box.
The limitation is stated plainly rather than hidden — each process keeps its own
buckets, so N workers allow N times the limit. That is acceptable for the goal
here, which is bounding abuse of endpoints that spend money or touch a third
party, not enforcing a billing quota.
"""

from __future__ import annotations

import time
from threading import Lock

from fastapi import HTTPException, status

#: Sweep dead buckets once the key count passes this. Bounds memory without
#: paying an O(keys) scan on every request.
_SWEEP_THRESHOLD = 1024


class SlidingWindowLimiter:
    """Per-key sliding window, e.g. 30 hits per 60 seconds per key."""

    def __init__(self, *, max_hits: int, window_sec: float, code: str, message: str):
        self.max_hits = max_hits
        self.window_sec = window_sec
        self.code = code
        self.message = message
        self._hits: dict[str, list[float]] = {}
        self._sweep_at = _SWEEP_THRESHOLD
        self._lock = Lock()

    def check(self, key: str) -> None:
        """Record a hit for `key`, or raise 429 if it is over budget."""
        now = time.monotonic()
        with self._lock:
            recent = [t for t in self._hits.get(key, ()) if now - t < self.window_sec]
            if len(recent) >= self.max_hits:
                # Keep the pruned list so the bucket does not grow without bound
                # on a key that keeps hammering the endpoint.
                self._hits[key] = recent
                retry_after = max(1, int(self.window_sec - (now - recent[0])) + 1)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={"code": self.code, "message": self.message},
                    headers={"Retry-After": str(retry_after)},
                )
            recent.append(now)
            self._hits[key] = recent
            if len(self._hits) >= self._sweep_at:
                self._sweep(now)
                # Amortise the scan: sweeping on every request once the dict is
                # over the threshold makes each check O(keys). Doubling the
                # trigger keeps the cost O(1) per insert on average.
                self._sweep_at = max(_SWEEP_THRESHOLD, len(self._hits) * 2)

    def _sweep(self, now: float) -> None:
        """Drop buckets with no hit inside the window.

        Without this the dict grows by one entry per distinct caller and never
        shrinks: the pruning inside `check` only touches the key being checked,
        so every IP that ever called stays resident for the process lifetime.
        """
        stale = [
            candidate
            for candidate, hits in self._hits.items()
            if not hits or now - hits[-1] >= self.window_sec
        ]
        for candidate in stale:
            del self._hits[candidate]

    def reset(self) -> None:
        """Drop all buckets. For tests, which share module state across cases."""
        with self._lock:
            self._hits.clear()
            self._sweep_at = _SWEEP_THRESHOLD


def client_key(request) -> str:
    """The bucket key for a request: the caller's IP, or 'unknown'."""
    client = getattr(request, "client", None)
    return client.host if client and client.host else "unknown"
