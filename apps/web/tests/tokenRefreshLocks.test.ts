/**
 * The `navigator.locks` branch of cross-tab refresh coordination.
 *
 * This is the path every current Chromium and Firefox build takes, so it is the
 * one real users hit — but jsdom has no LockManager, so the sibling test file
 * only exercises the localStorage-mutex fallback. A stub is installed here so
 * the primary path is covered rather than assumed.
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ApiError, authApi } from '../src/utils/api';

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

interface LockCall {
  name: string;
  mode?: string;
}

/**
 * A serialising LockManager stub: callbacks queue behind one another exactly as
 * a real implementation makes two tabs queue, and it records what was asked for.
 */
function installLockManager() {
  const calls: LockCall[] = [];
  let chain: Promise<unknown> = Promise.resolve();

  const manager = {
    request: vi.fn(
      async (name: string, options: unknown, callback: () => Promise<unknown>) => {
        const opts =
          typeof options === 'function' ? undefined : (options as { mode?: string } | undefined);
        const cb = (typeof options === 'function' ? options : callback) as () => Promise<unknown>;
        calls.push({ name, mode: opts?.mode });
        const run = chain.then(cb);
        chain = run.then(
          () => undefined,
          () => undefined,
        );
        return run;
      },
    ),
    query: vi.fn(async () => ({ held: [], pending: [] })),
  };

  Object.defineProperty(navigator, 'locks', {
    value: manager,
    configurable: true,
    writable: true,
  });

  return { manager, calls };
}

function removeLockManager() {
  // jsdom has no LockManager; leave the property absent rather than undefined so
  // the feature check (`navigator.locks && ...`) behaves like a real browser
  // that lacks it.
  try {
    delete (navigator as unknown as Record<string, unknown>).locks;
  } catch {
    Object.defineProperty(navigator, 'locks', { value: undefined, configurable: true });
  }
}

function spyFetch() {
  const counts = { refresh: 0, me: 0 };
  vi.spyOn(global, 'fetch').mockImplementation(async (input) => {
    const url = urlOf(input);
    if (url.includes('/auth/refresh')) {
      counts.refresh += 1;
      return jsonResponse(200, {});
    }
    counts.me += 1;
    return unauthorized();
  });
  return counts;
}

beforeEach(() => {
  window.localStorage.clear();
  vi.restoreAllMocks();
  vi.resetModules();
});

afterEach(() => {
  vi.restoreAllMocks();
  window.localStorage.clear();
  removeLockManager();
});

describe('cross-tab refresh under navigator.locks', () => {
  it('takes the exclusive named lock', async () => {
    const { calls } = installLockManager();
    spyFetch();

    await expect(authApi.getMe()).rejects.toBeInstanceOf(ApiError);

    expect(calls).toEqual([{ name: 'merit_token_refresh', mode: 'exclusive' }]);
  });

  it('refreshes once when two concurrent 401s race', async () => {
    installLockManager();
    const counts = spyFetch();

    const results = await Promise.allSettled([authApi.getMe(), authApi.getMe()]);

    expect(results.every((r) => r.status === 'rejected')).toBe(true);
    // The second one queues, finds the freshness stamp, and does not rotate the
    // cookie again — which on the server would read as token theft.
    expect(counts.refresh).toBe(1);
  });

  it('does not touch the localStorage mutex when the lock API exists', async () => {
    installLockManager();
    spyFetch();

    await expect(authApi.getMe()).rejects.toBeInstanceOf(ApiError);

    // The fallback key is only written by the fallback path.
    expect(window.localStorage.getItem('merit_refresh_lock_v1')).toBeNull();
  });

  it('still records the refresh stamp so a later tab can reuse it', async () => {
    installLockManager();
    spyFetch();

    await expect(authApi.getMe()).rejects.toBeInstanceOf(ApiError);

    const stamp = Number(window.localStorage.getItem('merit_refresh_at_v1'));
    expect(Number.isFinite(stamp)).toBe(true);
    expect(stamp).toBeGreaterThan(0);
  });
});
