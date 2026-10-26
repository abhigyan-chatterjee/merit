import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { AuthProvider } from '../src/store/AuthContext';
import { ProgressProvider, useProgress } from '../src/store/ProgressContext';

const PENDING_KEY = 'merit_pending_writes_v1';

const PROFILE = {
  id: 'u1',
  email: 'student@merit.org',
  display_name: 'Student One',
  displayName: 'Student One',
  role: 'user',
  created_at: '2026-01-01T00:00:00Z',
  last_login_at: null,
};

interface RecordedCall {
  url: string;
  init?: RequestInit;
}

function stubFetch(handler: (url: string) => unknown): RecordedCall[] {
  const calls: RecordedCall[] = [];
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      calls.push({ url, init });
      const body = await handler(url);
      return { ok: true, status: 200, statusText: '', json: async () => body };
    }),
  );
  return calls;
}

const Consumer: React.FC = () => {
  const { state, setProblemStatus, toggleBookmark, syncWithBackend } = useProgress();
  return (
    <div>
      <span data-testid="owner">{state.ownerUserId ?? 'none'}</span>
      <span data-testid="status">{state.progress['two-sum'] ?? 'none'}</span>
      <span data-testid="bookmarks">{state.bookmarks.join(',') || 'none'}</span>
      <span data-testid="quiz">{state.quizzes['arrays-hashing'] ?? 0}</span>
      <span data-testid="goal">{state.dailyGoal?.label ?? 'none'}</span>
      <button onClick={() => setProblemStatus('two-sum', 'Done')}>solve</button>
      <button onClick={() => toggleBookmark('two-sum')}>bookmark</button>
      <button onClick={() => void syncWithBackend()}>sync</button>
    </div>
  );
};

function renderApp() {
  return render(
    <AuthProvider>
      <ProgressProvider>
        <Consumer />
      </ProgressProvider>
    </AuthProvider>,
  );
}

const pendingWrites = (): unknown[] =>
  JSON.parse(window.localStorage.getItem(PENDING_KEY) ?? '[]') as unknown[];

describe('Progress sync resilience', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it('keeps a write made while the summary request is in flight', async () => {
    let releaseSummary: (value: unknown) => void = () => {};
    const summaryGate = new Promise<unknown>((resolve) => {
      releaseSummary = resolve;
    });

    const calls = stubFetch((url) => {
      if (url.includes('/auth/me')) return PROFILE;
      if (url.includes('/progress/summary')) return summaryGate;
      return {};
    });

    renderApp();

    // Wait until the summary request is actually outstanding.
    await waitFor(() =>
      expect(calls.some((c) => c.url.includes('/progress/summary'))).toBe(true),
    );

    fireEvent.click(screen.getByText('solve'));
    expect(screen.getByTestId('status')).toHaveTextContent('Done');

    // The server snapshot still says Todo — it was taken before the click.
    await act(async () => {
      releaseSummary({
        has_imported_local: true,
        progress: { 'two-sum': 'Todo' },
        notes: {},
        activity_days: {},
        visited_visualizers: [],
        bookmarks: [],
      });
    });

    // `owner` is only written when the snapshot is applied, so waiting for it
    // proves the merge ran.
    await waitFor(() => expect(screen.getByTestId('owner')).toHaveTextContent('u1'));
    expect(screen.getByTestId('status')).toHaveTextContent('Done');
  });

  it('reads bookmarks, quiz scores and the daily goal back from the summary', async () => {
    stubFetch((url) => {
      if (url.includes('/auth/me')) return PROFILE;
      if (url.includes('/progress/summary')) {
        return {
          has_imported_local: true,
          progress: {},
          notes: {},
          activity_days: {},
          visited_visualizers: [],
          bookmarks: [
            { item_type: 'problem', item_id: 'two-sum' },
            { item_type: 'question', item_id: 'q-1' },
          ],
          quiz_scores: { 'arrays-hashing': 90 },
          daily_goal: { kind: 'problems', label: 'Solve 3 problems', target: 3, permanent: true },
        };
      }
      return {};
    });

    renderApp();

    await waitFor(() => expect(screen.getByTestId('bookmarks')).toHaveTextContent('two-sum'));
    expect(screen.getByTestId('bookmarks')).not.toHaveTextContent('q-1');
    expect(screen.getByTestId('quiz')).toHaveTextContent('90');
    expect(screen.getByTestId('goal')).toHaveTextContent('Solve 3 problems');
  });

  it('queues a write that fails offline and replays it on the next sync', async () => {
    let online = false;
    const calls = stubFetch((url) => {
      if (url.includes('/auth/me')) return PROFILE;
      if (url.includes('/progress/summary')) {
        return {
          has_imported_local: true,
          progress: {},
          notes: {},
          activity_days: {},
          visited_visualizers: [],
          bookmarks: [],
        };
      }
      if (url.includes('/progress/problems/')) {
        if (!online) throw new Error('network down');
        return { problem_slug: 'two-sum', status: 'Done', updated_at: '2026-10-20T00:00:00Z' };
      }
      return {};
    });

    renderApp();
    await waitFor(() => expect(screen.getByTestId('owner')).toHaveTextContent('u1'));

    fireEvent.click(screen.getByText('solve'));

    // The request failed, but the write is persisted rather than dropped.
    await waitFor(() => expect(pendingWrites()).toHaveLength(1));
    const storedCalls = calls.filter((c) => c.url.includes('/progress/problems/'));
    expect(storedCalls).toHaveLength(1);

    online = true;
    fireEvent.click(screen.getByText('sync'));

    await waitFor(() => expect(pendingWrites()).toHaveLength(0));
    const replayed = calls.filter((c) => c.url.includes('/progress/problems/'));
    expect(replayed).toHaveLength(2);
    expect(screen.getByTestId('status')).toHaveTextContent('Done');
  });
});
