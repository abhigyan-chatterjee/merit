import { describe, it, expect, afterEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../src/store/AuthContext';
import { ProgressProvider, useProgress } from '../src/store/ProgressContext';

const PROFILE = {
  id: 'u1',
  email: 'student@merit.org',
  display_name: 'Student One',
  displayName: 'Student One',
  role: 'user',
  created_at: '2026-01-01T00:00:00Z',
  last_login_at: null,
};

/** Surfaces the synced slice so we can assert it settled to empty. */
const Consumer: React.FC = () => {
  const { user } = useAuth();
  const { state } = useProgress();
  return (
    <div>
      <span data-testid="user">{user ? user.displayName : 'guest'}</span>
      <span data-testid="streak">{state.streak.length}</span>
      <span data-testid="visited">{state.visitedVisualizers.length}</span>
      <span data-testid="solved">{Object.keys(state.progress).length}</span>
    </div>
  );
};

function stubFetch(summary: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : String(input);
      const body = url.includes('/auth/me') ? PROFILE : summary;
      return { ok: true, status: 200, statusText: '', json: async () => body };
    }),
  );
}

describe('ProgressContext backend sync', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    window.localStorage.clear();
  });

  it('degrades gracefully on a partial summary payload', async () => {
    // A truncated/partial 200 must not throw inside the provider — that would
    // blank the whole app for the affected user. The payload carries progress
    // but no activity_days, so an unguarded Object.keys() aborts the update and
    // the progress never lands.
    stubFetch({ has_imported_local: true, progress: { 'two-sum': 'Done' } });
    render(
      <AuthProvider>
        <ProgressProvider>
          <Consumer />
        </ProgressProvider>
      </AuthProvider>,
    );

    expect(await screen.findByText('Student One')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId('solved')).toHaveTextContent('1'));
    expect(screen.getByTestId('streak')).toHaveTextContent('0');
    expect(screen.getByTestId('visited')).toHaveTextContent('0');
  });

  it('applies a complete summary payload', async () => {
    stubFetch({
      has_imported_local: true,
      progress: { 'two-sum': 'Done' },
      notes: {},
      activity_days: { '2026-10-07': 1 },
      visited_visualizers: ['sorting'],
    });
    render(
      <AuthProvider>
        <ProgressProvider>
          <Consumer />
        </ProgressProvider>
      </AuthProvider>,
    );

    expect(await screen.findByText('Student One')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId('streak')).toHaveTextContent('1'));
    expect(screen.getByTestId('visited')).toHaveTextContent('1');
  });
});
