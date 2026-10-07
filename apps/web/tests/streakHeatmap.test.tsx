import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render } from '@testing-library/react';
import { StreakHeatmap } from '../src/components/StreakHeatmap';

const WEEKS = 18;

/** Fixed instant so the 18-week window is deterministic. */
const NOW = new Date(Date.UTC(2026, 9, 7, 12, 0, 0)); // 2026-10-07T12:00Z

/** All rendered day cells, which carry a YYYY-MM-DD title. */
function dayCells(container: HTMLElement): HTMLElement[] {
  return Array.from(container.querySelectorAll<HTMLElement>('div[title]')).filter((el) =>
    /^\d{4}-\d{2}-\d{2}/.test(el.getAttribute('title') ?? ''),
  );
}

/** The two numeric readouts: [activeDays, currentStreak]. */
function readouts(container: HTMLElement): string[] {
  return Array.from(container.querySelectorAll<HTMLElement>('.tnum')).map(
    (el) => el.textContent ?? '',
  );
}

describe('StreakHeatmap', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(NOW);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders a full 18-week grid', () => {
    const { container } = render(<StreakHeatmap streakDates={[]} currentStreak={0} />);
    expect(dayCells(container)).toHaveLength(WEEKS * 7);
  });

  it('marks the active day and counts it', () => {
    const { container } = render(
      <StreakHeatmap streakDates={['2026-10-07']} currentStreak={1} />,
    );

    const todayCell = dayCells(container).find(
      (el) => el.getAttribute('title') === '2026-10-07 — active session',
    );
    expect(todayCell).toBeDefined();
    expect(readouts(container)).toEqual(['1', '1']);
  });

  it('keys cells by UTC date, not local date', () => {
    // A day key produced by getUTCDateString must land on the matching cell.
    // If cells were keyed by a local-date conversion, a date recorded in UTC
    // would fall on the wrong column for non-UTC viewers.
    const utcKey = '2026-10-07';
    const { container } = render(<StreakHeatmap streakDates={[utcKey]} currentStreak={1} />);
    const cell = dayCells(container).find(
      (el) => el.getAttribute('title') === utcKey + ' — active session',
    );
    expect(cell).toBeDefined();
    expect(readouts(container)[0]).toBe('1');
  });

  it('ignores dates outside the window', () => {
    const { container } = render(
      <StreakHeatmap
        streakDates={['2026-10-07', '2026-10-06', '2025-01-01']}
        currentStreak={2}
      />,
    );
    expect(dayCells(container).map((el) => el.getAttribute('title'))).not.toContain(
      '2025-01-01 — active session',
    );
    expect(readouts(container)[0]).toBe('2');
  });

  it('flags days after today as future with no activity label', () => {
    const { container } = render(<StreakHeatmap streakDates={[]} currentStreak={0} />);
    const tomorrow = '2026-10-08';
    const cell = dayCells(container).find((el) => el.getAttribute('title') === tomorrow);
    // Future cells carry the bare date; past/empty cells carry "no activity".
    expect(cell).toBeDefined();
    expect(cell?.getAttribute('title')).not.toContain('no activity');
  });

  it('showcases the streak alongside the activity count', () => {
    const { container } = render(<StreakHeatmap streakDates={['2026-10-07']} currentStreak={5} />);
    expect(readouts(container)).toEqual(['1', '5']);
  });
});
