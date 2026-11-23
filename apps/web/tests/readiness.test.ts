import { describe, it, expect } from 'vitest';
import { computeDaysToDrive, computePlacementReadiness, TARGET_TIER_META } from '../src/utils/readiness';

const fresh = {
  progress: {},
  quizzes: {},
  streakDays: 0,
  dueTodayCount: 0,
  targetTier: 'product' as const,
  targetDriveDate: null,
};

describe('readiness', () => {
  it('scores a fresh user as 0/100 Getting Started', () => {
    const r = computePlacementReadiness(fresh);
    expect(r.score).toBe(0);
    expect(r.band).toBe('Getting Started');
    expect(r.pillars).toEqual({ dsa: 0, quizzes: 0, exams: 0, consistency: 0 });
    expect(r.focusItems).toHaveLength(3);
  });

  it('scales tier difficulty: same progress scores higher on service than faang', () => {
    const progress: Record<string, string> = {
      'two-sum': 'Done',
      'contains-duplicate': 'Done',
      'valid-anagram': 'Done',
      'group-anagrams': 'Done',
      'subarray-sum-equals-k': 'Done',
    };
    const quizzes = { 'arrays-hashing': 80, aptitude: 70, 'exam:tcs-nqt': 65 };
    const base = { progress, quizzes, streakDays: 6, dueTodayCount: 0, targetDriveDate: null };
    const service = computePlacementReadiness({ ...base, targetTier: 'service' });
    const faang = computePlacementReadiness({ ...base, targetTier: 'faang' });
    expect(TARGET_TIER_META.service.solvedTarget).toBeLessThan(TARGET_TIER_META.faang.solvedTarget);
    expect(service.score).toBeGreaterThan(faang.score);
  });

  it('computes day deltas without DST drift', () => {
    expect(computeDaysToDrive('2026-12-01', '2026-11-23')).toBe(8);
    expect(computeDaysToDrive('2026-11-23', '2026-11-23')).toBe(0);
    expect(computeDaysToDrive('2026-11-20', '2026-11-23')).toBe(-3);
    expect(computeDaysToDrive(null, '2026-11-23')).toBeNull();
    expect(computeDaysToDrive('not-a-date', '2026-11-23')).toBeNull();
    expect(computeDaysToDrive('2026-02-30', '2026-11-23')).toBeNull();
  });

  it('prioritizes due reviews first', () => {
    const r = computePlacementReadiness({ ...fresh, dueTodayCount: 2 });
    expect(r.focusItems).toHaveLength(3);
    expect(r.focusItems[0].link).toBe('/review');
    expect(r.focusItems[0].title).toMatch(/2 due review/);
  });

  it('prioritizes the weakest sub-75 quiz topic and maps core-cs', () => {
    const r = computePlacementReadiness({
      ...fresh,
      quizzes: { 'arrays-hashing': 90, 'core-cs': 40 },
    });
    const links = r.focusItems.map((f) => f.link);
    expect(links).toContain('/quiz/cs-fundamentals');
    const weak = computePlacementReadiness({ ...fresh, quizzes: { 'dynamic-programming': 50 } });
    expect(weak.focusItems.map((f) => f.link)).toContain('/quiz/dynamic-programming');
  });

  it('suggests the aptitude quiz when nothing is taken', () => {
    const r = computePlacementReadiness(fresh);
    expect(r.focusItems.map((f) => f.link)).toContain('/quiz/aptitude');
  });

  it('always returns exactly 3 unique actionable items', () => {
    const scenarios = [
      fresh,
      { ...fresh, dueTodayCount: 3, quizzes: { 'arrays-hashing': 30 } },
      {
        ...fresh,
        targetTier: 'faang' as const,
        progress: { 'two-sum': 'Done' },
        quizzes: { 'arrays-hashing': 95, 'trees': 90, 'exam:full-mock': 88 },
        streakDays: 20,
      },
      {
        ...fresh,
        targetTier: 'service' as const,
        quizzes: { 'arrays-hashing': 95, aptitude: 90, verbal: 88, sql: 92 },
        streakDays: 10,
      },
    ];
    for (const s of scenarios) {
      const r = computePlacementReadiness(s);
      expect(r.focusItems).toHaveLength(3);
      const links = r.focusItems.map((f) => f.link);
      expect(new Set(links).size).toBe(3);
      for (const f of r.focusItems) {
        expect(f.link).toMatch(/^\/(review|quiz\/[^/]+|problems\/[^/]+\/[^/]+|exams\/[^/]+|learn.*)$/);
      }
    }
  });
});
