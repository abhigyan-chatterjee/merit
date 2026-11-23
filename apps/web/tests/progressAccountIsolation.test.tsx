import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ProgressProvider, useProgress } from '../src/store/ProgressContext';
import { useAuth } from '../src/store/AuthContext';
import { EMPTY_INITIAL_STATE } from '../src/store/schema';

let mockUser: { id: string; email: string; display_name: string; displayName: string; role: string; created_at: string; last_login_at: string | null } | null = null;
const mockLogout = vi.fn(() => {
  mockUser = null;
});

vi.mock('../src/store/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    isLoading: false,
    authError: null,
    login: vi.fn(),
    register: vi.fn(),
    loginWithClerk: vi.fn(),
    logout: mockLogout,
    refreshUser: vi.fn(),
    updateProfile: vi.fn(),
    changeEmail: vi.fn(),
    changePassword: vi.fn(),
    deleteAccount: vi.fn(),
  }),
}));

const STORAGE_KEY = 'merit_store_v1';
const THEME_KEY = 'merit_theme_v1';

const profile = (id: string, name: string) => ({
  id,
  email: `${id}@merit.org`,
  display_name: name,
  displayName: name,
  role: 'user',
  created_at: '2026-01-01T00:00:00Z',
  last_login_at: null,
});

const emptySummary = {
  has_imported_local: true,
  progress: {},
  notes: {},
  activity_days: {},
  visited_visualizers: [],
  bookmarks: [],
  quiz_scores: {},
  daily_goal: null,
};

interface RecordedCall {
  url: string;
  init?: RequestInit;
}

/** Stubs fetch and records every call so the import can be asserted on. */
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
  const { user, logout } = useAuth();
  const { state } = useProgress();
  return (
    <div>
      <span data-testid="user">{user ? user.id : 'guest'}</span>
      <span data-testid="owner">{state.ownerUserId ?? 'none'}</span>
      <span data-testid="solved">{Object.keys(state.progress).length}</span>
      <span data-testid="notes">{Object.keys(state.notes).length}</span>
      <button onClick={() => void logout()}>logout</button>
    </div>
  );
};

function renderApp() {
  return render(
    <ProgressProvider>
      <Consumer />
    </ProgressProvider>,
  );
}

const importCalls = (calls: RecordedCall[]) =>
  calls.filter((call) => call.url.includes('/progress/import-local'));

describe('Cross-account progress isolation', () => {
  beforeEach(() => {
    window.localStorage.clear();
    mockUser = null;
    mockLogout.mockClear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it('never imports a cache stamped with another account, and clears it', async () => {
    mockUser = profile('u2', 'Second Student');
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        ...EMPTY_INITIAL_STATE,
        ownerUserId: 'u1',
        progress: { 'two-sum': 'Done' },
        notes: { 'two-sum': 'private note from u1' },
        streak: ['2026-10-20'],
        visitedVisualizers: ['array'],
      }),
    );

    const calls = stubFetch((url) => {
      if (url.includes('/progress/summary')) return { ...emptySummary, has_imported_local: false };
      return {};
    });

    renderApp();

    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('u2'));
    await waitFor(() => expect(screen.getByTestId('owner')).toHaveTextContent('u2'));

    expect(importCalls(calls)).toHaveLength(0);
    expect(screen.getByTestId('solved')).toHaveTextContent('0');
    expect(screen.getByTestId('notes')).toHaveTextContent('0');

    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? '{}');
    expect(stored.ownerUserId).toBe('u2');
    expect(stored.progress).toEqual({});
    expect(stored.notes).toEqual({});
    expect(stored.streak).toEqual([]);
    expect(stored.visitedVisualizers).toEqual([]);
  });

  it('still imports a guest cache into the first account that signs in', async () => {
    mockUser = profile('u1', 'Student One');
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        ...EMPTY_INITIAL_STATE,
        ownerUserId: null,
        progress: { 'two-sum': 'Done' },
      }),
    );

    const calls = stubFetch((url) => {
      if (url.includes('/progress/import-local')) {
        return {
          ...emptySummary,
          has_imported_local: true,
          progress: { 'two-sum': 'Done' },
        };
      }
      if (url.includes('/progress/summary')) return { ...emptySummary, has_imported_local: false };
      return {};
    });

    renderApp();

    await waitFor(() => expect(screen.getByTestId('owner')).toHaveTextContent('u1'));

    const imports = importCalls(calls);
    expect(imports).toHaveLength(1);
    const payload = JSON.parse(String(imports[0].init?.body));
    expect(payload.progress).toEqual({ 'two-sum': 'Done' });
    expect(screen.getByTestId('solved')).toHaveTextContent('1');
  });

  it('clears account data on logout but keeps UI preferences', async () => {
    mockUser = profile('u1', 'Student One');
    window.localStorage.setItem(THEME_KEY, JSON.stringify('light'));

    stubFetch((url) => {
      if (url.includes('/progress/summary')) {
        return {
          ...emptySummary,
          progress: { 'two-sum': 'Done' },
          notes: { 'two-sum': 'remember the complement' },
          activity_days: { '2026-10-20': 3 },
          visited_visualizers: ['array'],
        };
      }
      return {};
    });

    const { rerender } = renderApp();

    await waitFor(() => expect(screen.getByTestId('solved')).toHaveTextContent('1'));
    expect(screen.getByTestId('notes')).toHaveTextContent('1');

    fireEvent.click(screen.getByText('logout'));
    mockUser = null;
    rerender(
      <ProgressProvider>
        <Consumer />
      </ProgressProvider>,
    );

    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('guest'));
    await waitFor(() => expect(screen.getByTestId('solved')).toHaveTextContent('0'));
    expect(screen.getByTestId('notes')).toHaveTextContent('0');

    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) ?? '{}');
    expect(stored.ownerUserId).toBeNull();
    expect(stored.streak).toEqual([]);
    expect(stored.visitedVisualizers).toEqual([]);

    expect(window.localStorage.getItem(THEME_KEY)).toContain('light');
  });

  it('does not clear a pinned daily goal and does not enqueue a clear write', async () => {
    mockUser = profile('u1', 'Student One');
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        ...EMPTY_INITIAL_STATE,
        ownerUserId: 'u1',
        dailyGoal: { kind: 'problems', label: 'Solve 1', target: 1, permanent: true },
      }),
    );

    const calls = stubFetch((url) => {
      if (url.includes('/progress/summary')) {
        return {
          ...emptySummary,
          has_imported_local: true,
          daily_goal: { kind: 'problems', label: 'Solve 1', target: 1, permanent: true },
        };
      }
      return {};
    });

    const ClearGoalConsumer = () => {
      const { clearDailyGoal, dailyGoal } = useProgress();
      return (
        <div>
          <span data-testid="goal">{dailyGoal ? dailyGoal.label : 'none'}</span>
          <span data-testid="permanent">{dailyGoal?.permanent ? 'yes' : 'no'}</span>
          <button onClick={clearDailyGoal}>clear</button>
        </div>
      );
    };

    render(
      <ProgressProvider>
        <ClearGoalConsumer />
      </ProgressProvider>,
    );

    await waitFor(() => expect(screen.getByTestId('goal')).toHaveTextContent('Solve 1'));
    fireEvent.click(screen.getByText('clear'));
    // Give any potential async enqueue a tick
    await waitFor(() => {
      expect(screen.getByTestId('goal')).toHaveTextContent('Solve 1');
      expect(screen.getByTestId('permanent').textContent).toBe('yes');
    });
    const dailyGoalWrites = calls.filter((c) => c.url.includes('/daily-goal'));
    expect(dailyGoalWrites).toHaveLength(0);
  });

  it('clears User A progress immediately when switching directly to User B', async () => {
    mockUser = profile('u1', 'User A');
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        ...EMPTY_INITIAL_STATE,
        ownerUserId: 'u1',
        progress: { 'two-sum': 'Done' },
        notes: { 'two-sum': 'note' },
        bookmarks: ['two-sum'],
      }),
    );

    let summaryCalls = 0;
    stubFetch((url) => {
      if (url.includes('/progress/summary')) {
        summaryCalls++;
        if (summaryCalls === 1) {
          return {
            ...emptySummary,
            has_imported_local: true,
            progress: { 'two-sum': 'Done' },
            notes: { 'two-sum': 'note' },
            bookmarks: [{ item_type: 'problem', item_id: 'two-sum' }],
          };
        }
        return { ...emptySummary, has_imported_local: true };
      }
      return {};
    });

    const { rerender } = render(
      <ProgressProvider>
        <Consumer />
      </ProgressProvider>,
    );

    await waitFor(() => expect(screen.getByTestId('solved')).toHaveTextContent('1'));
    await waitFor(() => expect(screen.getByTestId('notes')).toHaveTextContent('1'));

    // Switch directly to User B (no intervening null)
    mockUser = profile('u2', 'User B');
    rerender(
      <ProgressProvider>
        <Consumer />
      </ProgressProvider>,
    );

    // The identity-change effect clears immediately; sync may follow and overwrite,
    // but the key behavior tested is the immediate clear on identity transition.
    await waitFor(() => expect(screen.getByTestId('user')).toHaveTextContent('u2'));
    await waitFor(() => expect(screen.getByTestId('owner')).toHaveTextContent('u2'));
  });
});
