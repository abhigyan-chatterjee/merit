import { describe, it, expect, beforeEach, vi } from 'vitest';
import { authApi, ApiError } from '../src/utils/api';

beforeEach(() => {
  vi.restoreAllMocks();
});

describe('api 401 refresh handshake under real races', () => {
  it('two concurrent 401s share one refresh attempt and never double-retry', async () => {
    const fail401 = () =>
      Promise.resolve({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: async () => ({ error: { code: 'SESSION_EXPIRED', message: 'no session' } }),
      } as Response);

    // Calls in order: A -> B -> refresh. The refresh fails, so joined requests
    // must not trigger a third original-call retry for either request.
    const fetchSpy = vi
      .spyOn(global, 'fetch')
      .mockImplementation(async (input) => {
        const url = typeof input === 'string' ? input : (input as Request).url;
        if (url.includes('/auth/refresh')) {
          return { ok: false, status: 500, json: async () => ({}) } as Response;
        }
        return fail401();
      });

    const [a, b] = await Promise.allSettled([authApi.getMe(), authApi.getMe()]);
    expect(a.status).toBe('rejected');
    expect(b.status).toBe('rejected');
    expect((b as PromiseRejectedResult).reason).toBeInstanceOf(ApiError);

    // Exactly three fetches: two original requests plus ONE shared refresh.
    const urls = fetchSpy.mock.calls.map((c) => {
      const u = c[0];
      return typeof u === 'string' ? u : (u as Request).url;
    });
    const refreshCalls = urls.filter((u) => u.includes('/auth/refresh'));
    const originalCalls = urls.filter((u) => u.includes('/auth/me'));
    expect(refreshCalls.length).toBe(1);
    expect(originalCalls.length).toBe(2);
  });
});
