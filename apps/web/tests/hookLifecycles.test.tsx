import React from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { getUTCDateString, useStreak } from '../src/hooks/useStreak';
import { useDebouncedCallback } from '../src/hooks/useDebouncedCallback';
import { useLocalStorage } from '../src/hooks/useLocalStorage';

describe('Hook lifecycles', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  describe('useStreak day key', () => {
    it('rolls the day key over at UTC midnight without a reload', () => {
      vi.useFakeTimers();
      // 26 Oct 2026, 23:59:30 UTC.
      vi.setSystemTime(new Date(Date.UTC(2026, 9, 26, 23, 59, 30)));

      const record = vi.fn();
      const { result } = renderHook(() => useStreak([], record));
      expect(result.current.today).toBe('2026-10-26');

      act(() => {
        vi.advanceTimersByTime(60_000);
      });

      expect(result.current.today).toBe('2026-10-27');

      // Activity is credited to the new day, not the one the tab opened on.
      act(() => {
        result.current.markTodayActive();
      });
      expect(record).toHaveBeenCalledWith('2026-10-27');
    });

    it('picks the new day up when the tab becomes visible again', () => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date(Date.UTC(2026, 9, 26, 12, 0, 0)));

      const { result } = renderHook(() => useStreak([], vi.fn()));
      expect(result.current.today).toBe('2026-10-26');

      // The tab slept past midnight: the clock moved, the interval did not run.
      vi.setSystemTime(new Date(Date.UTC(2026, 9, 27, 9, 0, 0)));
      act(() => {
        document.dispatchEvent(new Event('visibilitychange'));
      });

      expect(result.current.today).toBe('2026-10-27');
    });

    it('keeps counting a streak that includes yesterday across the rollover', () => {
      const yesterday = getUTCDateString(new Date(Date.now() - 86_400_000));
      const { result } = renderHook(() => useStreak([yesterday], vi.fn()));
      expect(result.current.currentStreak).toBe(1);
    });
  });

  describe('useDebouncedCallback', () => {
    it('fires once, with the latest arguments, after the delay', () => {
      vi.useFakeTimers();
      const spy = vi.fn();
      const { result } = renderHook(() => useDebouncedCallback(spy, 400));

      act(() => {
        result.current('a');
        result.current('ab');
        result.current('abc');
      });
      expect(spy).not.toHaveBeenCalled();

      act(() => {
        vi.advanceTimersByTime(399);
      });
      expect(spy).not.toHaveBeenCalled();

      act(() => {
        vi.advanceTimersByTime(1);
      });
      expect(spy).toHaveBeenCalledTimes(1);
      expect(spy).toHaveBeenCalledWith('abc');
    });

    it('cancels a pending call on unmount', () => {
      vi.useFakeTimers();
      const spy = vi.fn();
      const { result, unmount } = renderHook(() => useDebouncedCallback(spy, 400));

      act(() => {
        result.current('discarded');
      });
      unmount();

      act(() => {
        vi.advanceTimersByTime(1_000);
      });
      expect(spy).not.toHaveBeenCalled();
    });
  });

  describe('useLocalStorage persistence', () => {
    it('writes once per committed value, not once per updater invocation', () => {
      const key = 'merit_test_write_once';
      const setItem = vi.spyOn(Storage.prototype, 'setItem');

      // StrictMode invokes state updaters twice in development; the write must
      // not be inside the updater.
      const { result } = renderHook(() => useLocalStorage<{ n: number }>(key, { n: 0 }), {
        wrapper: ({ children }) => <React.StrictMode>{children}</React.StrictMode>,
      });

      let updaterCalls = 0;
      act(() => {
        result.current[1]((prev) => {
          updaterCalls += 1;
          return { ...prev, n: 1 };
        });
      });

      const writes = setItem.mock.calls.filter(([writtenKey]) => writtenKey === key);
      expect(writes).toHaveLength(1);
      expect(writes[0][1]).toBe(JSON.stringify({ n: 1 }));
      expect(updaterCalls).toBeGreaterThanOrEqual(1);

      setItem.mockRestore();
    });

    it('does not rewrite the value it just read on mount', () => {
      const key = 'merit_test_no_mount_write';
      window.localStorage.setItem(key, JSON.stringify({ n: 7 }));
      const setItem = vi.spyOn(Storage.prototype, 'setItem');

      const { result } = renderHook(() => useLocalStorage<{ n: number }>(key, { n: 0 }));

      expect(result.current[0]).toEqual({ n: 7 });
      expect(setItem.mock.calls.filter(([writtenKey]) => writtenKey === key)).toHaveLength(0);

      setItem.mockRestore();
    });
  });
});
