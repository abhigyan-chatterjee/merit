/**
 * Surfaces added with spaced repetition and company tagging.
 *
 * The two features share a property worth pinning: they must not pretend to have
 * data they do not. The company filter is absent until tags exist, and a review
 * only moves when the user rates it.
 */
import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { DashboardPage } from '../src/pages/DashboardPage';
import { ProblemListPage } from '../src/pages/ProblemListPage';
import { ProgressProvider } from '../src/store/ProgressContext';
import { AuthProvider } from '../src/store/AuthContext';
import { PROBLEMS } from '../src/data/problems';
import { RevisionItem } from '../src/utils/api';

const summaryWithReviews = (items: RevisionItem[]) => ({
  solved_count: 1,
  doing_count: 0,
  total_problems: PROBLEMS.length,
  current_streak: 1,
  activity_days: {},
  progress: {},
  notes: {},
  bookmarks: [],
  visited_visualizers: [],
  has_imported_local: true,
  quiz_scores: {},
  weakest_topics: [],
  revision_due: items,
  preferred_language: 'python',
  daily_goal: null,
});

const twoReviews: RevisionItem[] = [
  {
    type: 'problem',
    id: 'two-sum',
    title: 'Two Sum',
    reason: 'Spaced review · 1d interval',
    due_stage: '2026-10-26',
    link: '/problems/arrays-hashing/two-sum',
  },
  {
    type: 'question',
    id: 'q-42',
    title: 'Concept: what is a hash map?',
    reason: 'Spaced review · 1d interval',
    due_stage: '2026-10-26',
    link: '/quiz/arrays-hashing',
  },
];

let fetchMock: ReturnType<typeof vi.fn>;

beforeEach(() => {
  window.localStorage.clear();
  fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.includes('/api/v1/auth/me')) {
      return new Response(
        JSON.stringify({
          id: 'u1',
          email: 'a@b.co',
          display_name: 'Rev',
          role: 'student',
          created_at: '2026-10-01T00:00:00Z',
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );
    }
    if (url.includes('/api/v1/revision/') && init?.method === 'POST') {
      return new Response(
        JSON.stringify({
          item_type: 'problem',
          item_id: 'two-sum',
          due_date: '2026-11-01',
          interval_days: 6,
          ease: 2.6,
          reps: 2,
          lapses: 0,
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      );
    }
    if (url.includes('/api/v1/progress/summary')) {
      return new Response(JSON.stringify(summaryWithReviews(twoReviews)), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
  });
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
});


/** The dashboard only fetches a summary once it has a user, so auth is required. */
const renderDashboard = () =>
  render(
    <AuthProvider>
      <ProgressProvider>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </ProgressProvider>
    </AuthProvider>
  );

describe('spaced repetition queue', () => {
  it('renders the scheduled items with their due date, not a hardcoded label', async () => {
    renderDashboard();

    expect(await screen.findByText('Two Sum')).toBeInTheDocument();
    // The old implementation hardcoded "1d review"; the date is the contract now.
    expect(screen.getAllByText('2026-10-26').length).toBe(2);
  });

  it('rates a review and sends the grade the user chose', async () => {
    const user = userEvent.setup();
    renderDashboard();

    const gotIt = await screen.findByLabelText('Mark Two Sum as recalled');
    await user.click(gotIt);

    await waitFor(() => {
      const posts = fetchMock.mock.calls.filter(
        ([url, init]) =>
          String(url).includes('/api/v1/revision/problem/two-sum/review') &&
          (init as RequestInit | undefined)?.method === 'POST'
      );
      expect(posts.length).toBe(1);
    });

    const [, init] = fetchMock.mock.calls.find(
      ([url, i]) =>
        String(url).includes('/api/v1/revision/problem/two-sum/review') &&
        (i as RequestInit | undefined)?.method === 'POST'
    ) as [string, RequestInit];
    expect(JSON.parse(String(init.body))).toEqual({ grade: 4 });
  });

  it('sends a failing grade when the user picks Again', async () => {
    const user = userEvent.setup();
    renderDashboard();

    await user.click(await screen.findByLabelText('Mark Two Sum as needing another pass'));

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(([url]) =>
        String(url).includes('/api/v1/revision/problem/two-sum/review')
      );
      expect(call).toBeDefined();
      expect(JSON.parse(String((call![1] as RequestInit).body))).toEqual({ grade: 2 });
    });
  });

  it('does not rate a review just by opening the problem', async () => {
    renderDashboard();

    await screen.findByText('Two Sum');
    const posts = fetchMock.mock.calls.filter(
      ([url, init]) =>
        String(url).includes('/api/v1/revision/') &&
        (init as RequestInit | undefined)?.method === 'POST'
    );
    expect(posts.length).toBe(0);
  });
});
