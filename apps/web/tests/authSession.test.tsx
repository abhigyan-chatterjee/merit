import { describe, it, expect, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../src/store/AuthContext';

const PROFILE_BODY = {
  id: 'u1',
  email: 'student@merit.org',
  display_name: 'Student One',
  displayName: 'Student One',
  role: 'user',
  created_at: '2026-01-01T00:00:00Z',
  last_login_at: null,
};

const Consumer: React.FC = () => {
  const { user, authError, isLoading, refreshUser } = useAuth();
  return (
    <div>
      <span data-testid="user">{user ? user.email : 'guest'}</span>
      <span data-testid="error">{authError ? authError.message : 'none'}</span>
      <span data-testid="loading">{String(isLoading)}</span>
      <button onClick={() => void refreshUser()}>retry</button>
    </div>
  );
};

const jsonResponse = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

describe('Session probe error handling', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('clears the user on a real 401 without reporting an error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(401, { error: { code: 'UNAUTHORIZED', message: 'Not logged in' } })),
    );

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'));
    expect(screen.getByTestId('user')).toHaveTextContent('guest');
    expect(screen.getByTestId('error')).toHaveTextContent('none');
  });

  it('surfaces a retryable error instead of assuming the session died on a 5xx', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        jsonResponse(500, { error: { code: 'INTERNAL_ERROR', message: 'boom' } }),
      ),
    );

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'));
    expect(screen.getByTestId('error')).toHaveTextContent('boom');
  });

  it('surfaces a retryable error when the probe cannot reach the network', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch');
      }),
    );

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId('loading')).toHaveTextContent('false'));
    expect(screen.getByTestId('user')).toHaveTextContent('guest');
    expect(screen.getByTestId('error')).toHaveTextContent('Failed to fetch');
  });

  it('recovers on retry once the probe succeeds', async () => {
    let healthy = false;
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        healthy
          ? jsonResponse(200, PROFILE_BODY)
          : jsonResponse(503, { error: { code: 'UNAVAILABLE', message: 'try later' } }),
      ),
    );

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    );

    await waitFor(() => expect(screen.getByTestId('error')).toHaveTextContent('try later'));

    healthy = true;
    fireEvent.click(screen.getByText('retry'));

    await waitFor(() =>
      expect(screen.getByTestId('user')).toHaveTextContent('student@merit.org'),
    );
    expect(screen.getByTestId('error')).toHaveTextContent('none');
  });
});
