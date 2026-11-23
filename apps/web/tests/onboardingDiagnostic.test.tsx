import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { DashboardPage } from '../src/pages/DashboardPage';
import { QuizPage } from '../src/pages/QuizPage';
import { ProgressProvider } from '../src/store/ProgressContext';
import { DIAGNOSTIC_QUESTIONS } from '../src/components/OnboardingDiagnostic';

function stubGuestFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: async () => ({ error: { code: 'UNAUTHENTICATED', message: 'no session' } }),
    }),
  );
}

describe('OnboardingDiagnostic', () => {
  beforeEach(() => {
    window.localStorage.clear();
    stubGuestFetch();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('has exactly 12 questions, 3 per pillar across 4 topics', () => {
    expect(DIAGNOSTIC_QUESTIONS).toHaveLength(12);
    for (const topic of ['arrays-hashing', 'trees', 'cs-fundamentals', 'aptitude'] as const) {
      expect(DIAGNOSTIC_QUESTIONS.filter((q) => q.topic === topic)).toHaveLength(3);
    }
    for (const q of DIAGNOSTIC_QUESTIONS) {
      expect(q.options).toHaveLength(4);
      expect(q.correctIndex).toBeGreaterThanOrEqual(0);
      expect(q.correctIndex).toBeLessThan(4);
    }
  });

  it('scores all-correct run from DashboardPage, saves pillar scores and applies recommended tier', () => {
    render(
      <ProgressProvider>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </ProgressProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: /Take 12-Q Calibration Diagnostic/i }));
    expect(screen.getByRole('dialog', { name: '12-Question Placement Diagnostic' })).toBeInTheDocument();
    expect(screen.getByText(/Q1 ·/)).toBeInTheDocument();

    for (let i = 0; i < DIAGNOSTIC_QUESTIONS.length; i++) {
      const q = DIAGNOSTIC_QUESTIONS[i];
      const dialog = screen.getByRole('dialog', { name: '12-Question Placement Diagnostic' });
      const correctText = q.options[q.correctIndex];
      const btn = Array.from(dialog.querySelectorAll('button')).find((b) =>
        b.textContent?.includes(correctText),
      );
      expect(btn).toBeTruthy();
      fireEvent.click(btn!);
      if (i < DIAGNOSTIC_QUESTIONS.length - 1) {
        fireEvent.click(screen.getByRole('button', { name: /Next →/ }));
      }
    }

    fireEvent.click(screen.getByRole('button', { name: 'Finish Diagnostic' }));

    expect(screen.getByText(/12\/12/)).toBeInTheDocument();
    expect(screen.getAllByText(/100%/).length).toBeGreaterThanOrEqual(5);
    expect(screen.getAllByText(/3\/3/).length).toBeGreaterThanOrEqual(4);
    expect(screen.getAllByText(/FAANG & Dream/).length).toBeGreaterThanOrEqual(1);
    expect(window.localStorage.getItem('merit_onboarding_diag_done_v1')).toBeTruthy();

    const stored = JSON.parse(window.localStorage.getItem('merit_store_v1') ?? '{}');
    expect(stored.quizzes['arrays-hashing']).toBe(100);
    expect(stored.quizzes['trees']).toBe(100);
    expect(stored.quizzes['cs-fundamentals']).toBe(100);
    expect(stored.quizzes['aptitude']).toBe(100);

    fireEvent.click(screen.getByRole('button', { name: 'Apply Recommended Tier' }));
    expect(screen.getByText('Tier applied!')).toBeInTheDocument();
    const afterApply = JSON.parse(window.localStorage.getItem('merit_store_v1') ?? '{}');
    expect(afterApply.targetTier).toBe('faang');

    fireEvent.click(screen.getByRole('button', { name: 'Done' }));
    expect(screen.queryByRole('dialog', { name: '12-Question Placement Diagnostic' })).not.toBeInTheDocument();
  });

  it('opens from QuizPage and closes via Close diagnostic', () => {
    render(
      <ProgressProvider>
        <MemoryRouter initialEntries={['/quiz/arrays-hashing']}>
          <Routes>
            <Route path="/quiz/:topic" element={<QuizPage />} />
          </Routes>
        </MemoryRouter>
      </ProgressProvider>,
    );

    fireEvent.click(screen.getByRole('button', { name: '12-Q Diagnostic' }));
    expect(screen.getByRole('dialog', { name: '12-Question Placement Diagnostic' })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Close diagnostic' }));
    expect(screen.queryByRole('dialog', { name: '12-Question Placement Diagnostic' })).not.toBeInTheDocument();
  });
});
