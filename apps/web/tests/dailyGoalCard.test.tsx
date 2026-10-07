import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { DailyGoalCard } from '../src/components/DailyGoalCard';
import { ProgressProvider } from '../src/store/ProgressContext';

const STORAGE_KEY = 'merit_store_v1';

function renderCard() {
  return render(
    <ProgressProvider>
      <DailyGoalCard />
    </ProgressProvider>,
  );
}

function stored(): Record<string, unknown> {
  return JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? '{}');
}

describe('DailyGoalCard', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('shows an empty state before a goal is chosen', () => {
    renderCard();
    expect(screen.getByText(/No goal yet/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Set goal/i })).toBeInTheDocument();
  });

  it('offers the presets when opened', () => {
    renderCard();
    fireEvent.click(screen.getByRole('button', { name: /Set goal/i }));
    expect(screen.getByRole('button', { name: 'Solve 3 problems' })).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: 'Score at least 7/10 in a quiz' }),
    ).toBeInTheDocument();
  });

  it('selects a preset and tracks progress against its target', () => {
    renderCard();
    fireEvent.click(screen.getByRole('button', { name: /Set goal/i }));
    fireEvent.click(screen.getByRole('button', { name: 'Solve 3 problems' }));

    expect(screen.getByText('Solve 3 problems')).toBeInTheDocument();
    expect(screen.getByText('0/3 solved today')).toBeInTheDocument();
    const goal = stored().dailyGoal as { kind: string; target: number };
    expect(goal).toMatchObject({ kind: 'problems', target: 3 });
  });

  it('adds a custom goal with manual check-off', () => {
    renderCard();
    fireEvent.click(screen.getByRole('button', { name: /Set goal/i }));
    fireEvent.change(screen.getByLabelText('Custom daily goal'), {
      target: { value: 'Revise DP notes 20 min' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Add custom goal' }));

    expect(screen.getByText('Revise DP notes 20 min')).toBeInTheDocument();
    expect(screen.getByText(/manual check-off/i)).toBeInTheDocument();
  });

  it('marks a custom goal done and back', () => {
    renderCard();
    fireEvent.click(screen.getByRole('button', { name: /Set goal/i }));
    fireEvent.click(screen.getByRole('button', { name: 'Custom goal (manual check-off)' }));

    const toggle = screen.getByRole('button', { name: /Mark done/i });
    expect(toggle).toHaveAttribute('aria-pressed', 'false');
    fireEvent.click(toggle);
    expect(screen.getByRole('button', { name: /Done/i })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
  });

  it('clears the goal back to the empty state', () => {
    renderCard();
    fireEvent.click(screen.getByRole('button', { name: /Set goal/i }));
    fireEvent.click(screen.getByRole('button', { name: 'Solve 1 problem' }));
    expect(screen.queryByText(/No goal yet/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Change/i }));
    fireEvent.click(screen.getByRole('button', { name: /Clear goal/i }));
    expect(screen.getByText(/No goal yet/i)).toBeInTheDocument();
    expect(stored().dailyGoal).toBeNull();
  });
});
