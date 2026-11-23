import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { AuthProvider } from '../src/store/AuthContext';
import { ProgressProvider, useProgress } from '../src/store/ProgressContext';

const Probe: React.FC = () => {
  const ctx = useProgress();
  return (
    <div>
      <span data-testid="progress">{ctx.dailyGoalProgressToday}</span>
      <span data-testid="done">{String(ctx.isDailyGoalDone)}</span>
      <span data-testid="goal">{ctx.dailyGoal?.label ?? 'none'}</span>
      <button
        onClick={() => ctx.setDailyGoal({ kind: 'problems', label: 'Solve 3 problems', target: 3 })}
      >
        problems-goal
      </button>
      <button
        onClick={() => ctx.setDailyGoal({ kind: 'quiz-score', label: 'Score 70', target: 70 })}
      >
        quiz-goal
      </button>
      <button onClick={() => ctx.saveQuizScore('arrays-hashing', 90)}>quiz-90</button>
      <button onClick={() => ctx.setProblemStatus('two-sum', 'Done')}>solve</button>
    </div>
  );
};

describe('Daily goal progress scoping', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
        json: async () => ({ error: { code: 'UNAUTHENTICATED', message: 'guest' } }),
      }),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  const renderProbe = () =>
    render(
      <AuthProvider>
        <ProgressProvider>
          <Probe />
        </ProgressProvider>
      </AuthProvider>,
    );

  it('does not carry a completed quiz goal over to a smaller problems goal', () => {
    renderProbe();

    fireEvent.click(screen.getByText('quiz-goal'));
    fireEvent.click(screen.getByText('quiz-90'));

    // 90% clears the 70% target.
    expect(screen.getByTestId('progress')).toHaveTextContent('70');
    expect(screen.getByTestId('done')).toHaveTextContent('true');

    // A problems goal counts problems, not percentage points: the new goal
    // starts at 0 instead of inheriting 70 and looking already achieved.
    fireEvent.click(screen.getByText('problems-goal'));
    expect(screen.getByTestId('goal')).toHaveTextContent('Solve 3 problems');
    expect(screen.getByTestId('progress')).toHaveTextContent('0');
    expect(screen.getByTestId('done')).toHaveTextContent('false');

    fireEvent.click(screen.getByText('solve'));
    expect(screen.getByTestId('progress')).toHaveTextContent('1');
    expect(screen.getByTestId('done')).toHaveTextContent('false');
  });

  it('starts a quiz goal at 0 after problems were solved under a problems goal', () => {
    renderProbe();

    fireEvent.click(screen.getByText('problems-goal'));
    fireEvent.click(screen.getByText('solve'));
    expect(screen.getByTestId('progress')).toHaveTextContent('1');

    fireEvent.click(screen.getByText('quiz-goal'));
    expect(screen.getByTestId('progress')).toHaveTextContent('0');
    expect(screen.getByTestId('done')).toHaveTextContent('false');
  });
});
