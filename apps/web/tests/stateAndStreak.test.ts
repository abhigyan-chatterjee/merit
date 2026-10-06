import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { getUTCDateString } from '../src/hooks/useStreak';
import { useLocalStorage } from '../src/hooks/useLocalStorage';
import { EMPTY_INITIAL_STATE, ProgressStateZodSchema, ProgressStateSchema } from '../src/store/schema';

describe('State, Streak & Storage Resilience (D4, D7, D8, D9)', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  describe('D8: UTC Day Keys (timezone safety)', () => {
    it('keys the day by UTC date regardless of machine timezone', () => {
      // A moment near the UTC day boundary: 2026-09-08T02:00Z.
      const boundary = new Date(Date.UTC(2026, 8, 8, 2, 0, 0));
      expect(getUTCDateString(boundary)).toBe('2026-09-08');
    });

    it('rolls to the next UTC day at midnight UTC', () => {
      const beforeMidnight = new Date(Date.UTC(2026, 8, 8, 23, 59, 59));
      expect(getUTCDateString(beforeMidnight)).toBe('2026-09-08');
      const afterMidnight = new Date(Date.UTC(2026, 8, 9, 0, 0, 0));
      expect(getUTCDateString(afterMidnight)).toBe('2026-09-09');
    });
  });

  describe('D7: Honest Initial State', () => {
    it('initial state has empty streak, zero solved problems, and no fabricated records', () => {
      expect(EMPTY_INITIAL_STATE.streak).toEqual([]);
      expect(EMPTY_INITIAL_STATE.progress).toEqual({});
      expect(EMPTY_INITIAL_STATE.quizzes).toEqual({});
      expect(EMPTY_INITIAL_STATE.notes).toEqual({});
      expect(EMPTY_INITIAL_STATE.bookmarks).toEqual([]);
      expect(EMPTY_INITIAL_STATE.visitedVisualizers).toEqual([]);
    });
  });

  describe('D9: Storage Schema Validation & Safe Recovery', () => {
    it('recovers safely from completely corrupted JSON without crashing and saves backup', () => {
      const key = 'test_corrupted_key';
      const corruptedJson = '{"broken": [true, false, ';
      window.localStorage.setItem(key, corruptedJson);

      const { result } = renderHook(() =>
        useLocalStorage<ProgressStateSchema>(key, EMPTY_INITIAL_STATE, ProgressStateZodSchema)
      );

      // Successfully defaulted to initial state
      expect(result.current[0]).toEqual(EMPTY_INITIAL_STATE);

      // Preserved corrupted data in .backup key
      expect(window.localStorage.getItem(`${key}.backup`)).toBe(corruptedJson);
    });

    it('recovers safely from invalid schema / wrong types and saves backup', () => {
      const key = 'test_wrong_schema_key';
      // progress should be an object, not a string
      const invalidData = JSON.stringify({
        progress: 'totally-invalid-type',
        quizzes: { math: 100 },
      });
      window.localStorage.setItem(key, invalidData);

      const { result } = renderHook(() =>
        useLocalStorage<ProgressStateSchema>(key, EMPTY_INITIAL_STATE, ProgressStateZodSchema)
      );

      // Successfully reset to initial state
      expect(result.current[0]).toEqual(EMPTY_INITIAL_STATE);
      // Backup saved
      expect(window.localStorage.getItem(`${key}.backup`)).toBe(invalidData);
    });

    it('persists valid state updates correctly', () => {
      const key = 'test_valid_key';
      const { result } = renderHook(() =>
        useLocalStorage<ProgressStateSchema>(key, EMPTY_INITIAL_STATE, ProgressStateZodSchema)
      );

      act(() => {
        result.current[1]((prev) => ({
          ...prev,
          progress: { 'two-sum': 'Done' },
          visitedVisualizers: ['array', 'sorting'],
        }));
      });

      expect(result.current[0].progress['two-sum']).toBe('Done');
      expect(result.current[0].visitedVisualizers).toEqual(['array', 'sorting']);

      // Check localStorage
      const stored = JSON.parse(window.localStorage.getItem(key)!);
      expect(stored.progress['two-sum']).toBe('Done');
      expect(stored.visitedVisualizers).toEqual(['array', 'sorting']);
    });
  });
});
