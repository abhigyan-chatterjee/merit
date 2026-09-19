import { describe, it, test, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../src/store/AuthContext';
import { ProgressProvider } from '../src/store/ProgressContext';
import { GuidedPathsPage, usePathProgress } from '../src/pages/GuidedPathsPage';
import { renderHookForTest } from './testUtils';
import { PROBLEMS } from '../src/data/problems';
import foundationPath from '../../../content/paths/foundation.json';
import targetedPath from '../../../content/paths/targeted.json';
import masteryPath from '../../../content/paths/mastery.json';

function renderPage() {
  return render(
    <AuthProvider>
      <ProgressProvider>
        <MemoryRouter>
          <GuidedPathsPage />
        </MemoryRouter>
      </ProgressProvider>
    </AuthProvider>
  );
}

describe('Path progress consistency (/learn cards)', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('counts visited visualizers the same way as the detail page', () => {
    window.localStorage.setItem(
      'algovista_store_v1',
      JSON.stringify({
        progress: {
          'two-sum': 'Done',
          'contains-duplicate': 'Done',
        },
        quizzes: { 'arrays-hashing': 80 },
        streak: [],
        notes: {},
        bookmarks: [],
        dailyGoalDone: {},
        dailyGoal: null,
        dailyGoalProgress: {},
        visitedVisualizers: ['array'],
        lastVisited: null,
      })
    );

    const { result } = renderHookForTest(() => usePathProgress('foundation'));
    // Foundation: array viz + two-sum + contains-duplicate + arrays-hashing quiz = 4/20
    expect(result.current.done).toBe(4);
    expect(result.current.total).toBe(20);
    expect(result.current.pct).toBe(20);
  });

  it('renders one consistent percentage on the card (no 13% ghost)', () => {
    window.localStorage.setItem(
      'algovista_store_v1',
      JSON.stringify({
        progress: {
          'two-sum': 'Done',
          'contains-duplicate': 'Done',
        },
        quizzes: { 'arrays-hashing': 80 },
        streak: [],
        notes: {},
        bookmarks: [],
        dailyGoalDone: {},
        dailyGoal: null,
        dailyGoalProgress: {},
        visitedVisualizers: ['array'],
        lastVisited: null,
      })
    );

    renderPage();
    const card = screen.getByText('Foundation').closest('a')!;
    const pcts = within(card).getAllByText('20%');
    expect(pcts.length).toBeGreaterThanOrEqual(1);
    const countLabel = within(card).getByText((_content, el) => {
      if (!el || el.children.length > 0) return false;
      return (el.textContent ?? '').replace(/\s+/g, ' ').includes('4/20 complete');
    });
    expect(countLabel).toBeInTheDocument();
  });
});

describe('Path step resolution', () => {
  test('every problem step resolves to a verified problem', () => {
    const knownSlugs = new Set(PROBLEMS.map((p) => p.slug));
    const pathJsons = [foundationPath, targetedPath, masteryPath];

    for (const path of pathJsons) {
      for (const step of path.steps) {
        if (step.step_type === 'problem') {
          expect(
            knownSlugs.has(step.ref_id),
            `Dangling step ref '${step.ref_id}' in path '${path.slug}'`
          ).toBe(true);
        }
      }
    }
  });
});

describe('Daily goals', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('solving a problem bumps a problems-type goal toward done', async () => {
    const { ProgressProvider: P, useProgress } = await import(
      '../src/store/ProgressContext'
    );
    const Probe = () => {
      const ctx = useProgress();
      return (
        <div>
          <span data-testid="goal-progress">{ctx.dailyGoalProgressToday}</span>
          <span data-testid="goal-done">{String(ctx.isDailyGoalDone)}</span>
          <button
            onClick={() => ctx.setDailyGoal({ kind: 'problems', label: 'Solve 1 problem', target: 1 })}
          >
            set-goal
          </button>
          <button onClick={() => ctx.setProblemStatus('two-sum', 'Done')}>solve</button>
        </div>
      );
    };
    render(
      <AuthProvider>
        <P>
          <MemoryRouter>
            <Probe />
          </MemoryRouter>
        </P>
      </AuthProvider>
    );

    fireEvent.click(screen.getByText('set-goal'));
    expect(screen.getByTestId('goal-done').textContent).toBe('false');
    fireEvent.click(screen.getByText('solve'));
    expect(screen.getByTestId('goal-progress').textContent).toBe('1');
    expect(screen.getByTestId('goal-done').textContent).toBe('true');
  });
});
