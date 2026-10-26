import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ApiError, authApi } from '../src/utils/api';

const LOCK_KEY = 'merit_refresh_lock_v1';
const STAMP_KEY = 'merit_refresh_at_v1';

const jsonResponse = (status: number, body: unknown) =>
  ({
    ok: status >= 200 && status < 300,
    status,
    statusText: '',
    json: async () => body,
  }) as Response;

const unauthorized = () =>
  jsonResponse(401, { error: { code: 'SESSION_EXPIRED', message: 'no session' } });

function urlOf(input: RequestInfo | URL): string {
  return typeof input === 'string' ? input : String(input);
}

interface Counts {
  refresh: number;
  me: number;
}

function spyFetch(onRefresh: () => Response, onMe: () => Response) {
  const counts: Counts = { refresh: 0, me: 0 };
  vi.spyOn(global, 'fetch').mockImplementation(async (input) => {
    const url = urlOf(input);
    if (url.includes('/auth/refresh')) {
      counts.refresh += 1;
      return onRefresh();
    }
    counts.me += 1;
    return onMe();
  });
  return counts;
}

describe('Cross-tab token refresh', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
  });

  it('reuses a refresh another tab just completed instead of rotating again', async () => {
    // A neighbour refreshed 1s ago: rotating the same cookie again is what the
    // server reads as token theft and answers by revoking every session.
    window.localStorage.setItem(STAMP_KEY, String(Date.now() - 1_000));

    const counts = spyFetch(
      () => jsonResponse(200, {}),
      () => unauthorized(),
    );

    await expect(authApi.getMe()).rejects.toBeInstanceOf(ApiError);

    expect(counts.refresh).toBe(0);
    expect(counts.me).toBe(2);
  });

  it('takes over a lock left behind by a crashed tab and releases it', async () => {
    window.localStorage.setItem(
      LOCK_KEY,
      JSON.stringify({ id: 'crashed-tab', expiresAt: Date.now() - 5_000 }),
    );

    const counts = spyFetch(
      () => jsonResponse(200, {}),
      () => unauthorized(),
    );

    await expect(authApi.getMe()).rejects.toBeInstanceOf(ApiError);

    expect(counts.refresh).toBe(1);
    // The lock is released so the next expiry is not blocked by a dead entry...
    expect(window.localStorage.getItem(LOCK_KEY)).toBeNull();
    // ...and the refresh is stamped so other tabs do not rotate the cookie.
    expect(Number(window.localStorage.getItem(STAMP_KEY))).toBeGreaterThan(0);
  });

  it('waits for another tab that is mid-refresh rather than refreshing in parallel', async () => {
    window.localStorage.setItem(
      LOCK_KEY,
      JSON.stringify({ id: 'live-tab', expiresAt: Date.now() + 5_000 }),
    );

    // Stand in for the other tab finishing its refresh and dropping the lock.
    const neighbour = setTimeout(() => {
      window.localStorage.setItem(STAMP_KEY, String(Date.now()));
      window.localStorage.removeItem(LOCK_KEY);
    }, 30);

    const counts = spyFetch(
      () => jsonResponse(200, {}),
      () => unauthorized(),
    );

    try {
      await expect(authApi.getMe()).rejects.toBeInstanceOf(ApiError);
    } finally {
      clearTimeout(neighbour);
    }

    expect(counts.refresh).toBe(0);
    expect(counts.me).toBe(2);
  });
});
