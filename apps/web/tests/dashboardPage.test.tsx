import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { DashboardPage } from '../src/pages/DashboardPage';
import { ProgressProvider } from '../src/store/ProgressContext';
import { AuthProvider } from '../src/store/AuthContext';
import { PROBLEMS } from '../src/data/problems';
import { TOPICS } from '../src/data/curriculum';
import { LEARNING_PATHS } from '../src/data/learningPaths';

const FOUNDATION = LEARNING_PATHS.find((p) => p.id === 'foundation')!;

function mockFetch(user: boolean) {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes('/api/v1/auth/me')) {
      if (user) return new Response(JSON.stringify({ id: 'u1', email: 'a@b.co', display_name: 'U', role: 'student', created_at: '2026-10-01T00:00:00Z' }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      return new Response('{}', { status: 401 });
    }
    if (url.includes('/api/v1/progress/summary')) {
      return new Response(JSON.stringify({ solved_count: 0, doing_count: 0, total_problems: 0, current_streak: 0, activity_days: {}, progress: {}, notes: {}, bookmarks: [], visited_visualizers: [], has_imported_local: true, quiz_scores: {}, weakest_topics: [], revision_due: [], preferred_language: 'python', daily_goal: null }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }
    return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
  }));
}

describe('DashboardPage Honest Initial State (D7)', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('keeps the dashboard topic chart in placement-priority order', () => {
    expect(TOPICS.slice(0, 3).map((topic) => topic.slug)).toEqual([
      'arrays-hashing',
      'two-pointers',
      'sliding-windows',
    ]);
  });

  it('renders fresh user dashboard with 0s and "Start your first problem" CTA', () => {
    render(
      <ProgressProvider>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </ProgressProvider>
    );

    expect(screen.getAllByText(`0/${PROBLEMS.length}`).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('0d')).toBeInTheDocument();
    expect(screen.getAllByText(/Start your first problem/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/No assessment scores recorded yet/i)).toBeInTheDocument();
    expect(screen.getByText('Quizzes taken')).toBeInTheDocument();
    expect(screen.queryByText('Saved notes')).not.toBeInTheDocument();
  });

  it('shows path completion counts and percentages', () => {
    window.localStorage.setItem(
      'merit_store_v1',
      JSON.stringify({
        progress: { 'two-sum': 'Done', 'contains-duplicate': 'Done' },
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

    render(
      <ProgressProvider>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </ProgressProvider>
    );

    const foundation = screen.getByText('Foundation').closest('a');
    const done = 4;
    const pct = Math.round((done / FOUNDATION.steps.length) * 100);
    expect(foundation).toHaveTextContent(
      `${FOUNDATION.steps.length} steps · ${done}/${FOUNDATION.steps.length} complete · ${pct}%`
    );
  });

  it('hides reset button when signed in', async () => {
    mockFetch(true);
    render(
      <AuthProvider>
        <ProgressProvider>
          <MemoryRouter>
            <DashboardPage />
          </MemoryRouter>
        </ProgressProvider>
      </AuthProvider>
    );
    // Wait for a signed-in signal first: while auth is still resolving the
    // button is absent either way, so asserting immediately would pass falsely.
    expect(await screen.findByText('Welcome U')).toBeInTheDocument();
    expect(screen.queryByLabelText(/reset all locally stored progress/i)).not.toBeInTheDocument();
  });

  it('shows reset button when signed out', async () => {
    mockFetch(false);
    render(
      <AuthProvider>
        <ProgressProvider>
          <MemoryRouter>
            <DashboardPage />
          </MemoryRouter>
        </ProgressProvider>
      </AuthProvider>
    );
    expect(await screen.findByLabelText(/reset all locally stored progress/i)).toBeInTheDocument();
  });

  it('does not steal focus on initial mount when signed out', async () => {
    mockFetch(false);
    render(
      <AuthProvider>
        <ProgressProvider>
          <MemoryRouter>
            <DashboardPage />
          </MemoryRouter>
        </ProgressProvider>
      </AuthProvider>
    );
    const btn = await screen.findByLabelText(/reset all locally stored progress/i);
    expect(btn).not.toHaveFocus();
  });

  it('restores focus to reset button after closing confirm', async () => {
    mockFetch(false);
    render(
      <AuthProvider>
        <ProgressProvider>
          <MemoryRouter>
            <DashboardPage />
          </MemoryRouter>
        </ProgressProvider>
      </AuthProvider>
    );
    const btn = await screen.findByLabelText(/reset all locally stored progress/i);
    fireEvent.click(btn);
    const cancel = await screen.findByRole('button', { name: /cancel/i });
    fireEvent.click(cancel);
    await waitFor(() =>
      expect(screen.getByLabelText(/reset all locally stored progress/i)).toHaveFocus()
    );
  });
});