import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from '../src/store/AuthContext';
import { getLoginDestination, LoginPage } from '../src/pages/LoginPage';
import { RegisterPage } from '../src/pages/RegisterPage';
import { Navbar } from '../src/components/Navbar';
import { ProgressProvider } from '../src/store/ProgressContext';

const TestAuthConsumer = () => {
  const { user, login, logout, isLoading } = useAuth();
  if (isLoading) return <div>Loading...</div>;
  return (
    <div>
      <span data-testid="user-email">{user ? user.email : 'guest'}</span>
      <button onClick={() => login('test@merit.org', 'ValidPass123!')}>Login</button>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
};

describe('Auth Integration and UI', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it.each([
    '?next=https%3A%2F%2Fevil.example',
    '?next=%2F%2Fevil.example',
    '?next=%5C%2Fevil.example',
    '?next=%2F%5C%2Fevil.example',
    '?next=%20%2Fdashboard',
    '?next=%2F%2Fevil.example%2F%2E%2E%2Fdashboard',
  ])('rejects unsafe next destination %s', (search) => {
    expect(getLoginDestination({ search, state: { from: '/problems' } })).toBe('/problems');
  });

  it('preserves a safe next destination', () => {
    expect(getLoginDestination({ search: '?next=/exams', state: null })).toBe('/exams');
  });

  it('renders guest state when getMe returns 401', async () => {
    vi.spyOn(global, 'fetch').mockImplementation(async (url) => {
      if (String(url).includes('/auth/me')) {
        return new Response(JSON.stringify({ error: { code: 'UNAUTHORIZED', message: 'Not logged in' } }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      return new Response(JSON.stringify({}), { status: 200 });
    });

    render(
      <AuthProvider>
        <TestAuthConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user-email')).toHaveTextContent('guest');
    });
  });

  it('logs in successfully and updates user state', async () => {
    vi.spyOn(global, 'fetch').mockImplementation(async (url, init) => {
      if (String(url).includes('/auth/me')) {
        return new Response(JSON.stringify({ error: { code: 'UNAUTHORIZED' } }), { status: 401 });
      }
      if (String(url).includes('/auth/login')) {
        const body = JSON.parse(String(init?.body || '{}'));
        return new Response(
          JSON.stringify({
            user: {
              id: 'user_123',
              email: body.email,
              displayName: 'Ada Lovelace',
              role: 'student',
              isActive: true,
              createdAt: '2026-09-07T00:00:00Z',
              lastLoginAt: null,
            },
          }),
          { status: 200, headers: { 'Content-Type': 'application/json' } }
        );
      }
      return new Response(JSON.stringify({}), { status: 200 });
    });

    render(
      <AuthProvider>
        <TestAuthConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user-email')).toHaveTextContent('guest');
    });

    fireEvent.click(screen.getByText('Login'));

    await waitFor(() => {
      expect(screen.getByTestId('user-email')).toHaveTextContent('test@merit.org');
    });
  });

  it('renders Clerk-only registration without a native password input', async () => {
    vi.spyOn(global, 'fetch').mockImplementation(async () => {
      return new Response(JSON.stringify({ error: { code: 'UNAUTHORIZED' } }), { status: 401 });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <RegisterPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Create a MERIT Account/i)).toBeInTheDocument();
    });
    expect(document.querySelectorAll('input[type="password"]')).toHaveLength(0);
    expect(screen.getByText('Sign-in is not available in this environment.')).toBeInTheDocument();
    expect(screen.getByText('Set VITE_CLERK_PUBLISHABLE_KEY and rebuild.')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Sign in/i })).toBeInTheDocument();
  });

  it('renders Sign In in Navbar for guests', async () => {
    vi.spyOn(global, 'fetch').mockImplementation(async () => {
      return new Response(JSON.stringify({ error: { code: 'UNAUTHORIZED' } }), { status: 401 });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <ProgressProvider>
            <Navbar />
          </ProgressProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('link', { name: /Sign In/i })).toBeInTheDocument();
    });
  });

  it('does not flash Sign In while the session check is in flight', () => {
    vi.spyOn(global, 'fetch').mockImplementation(async (url) => {
      if (String(url).includes('/auth/me') || String(url).includes('/auth/refresh')) {
        return new Promise<Response>(() => {});
      }
      return new Response(JSON.stringify({}), { status: 200 });
    });

    render(
      <MemoryRouter>
        <AuthProvider>
          <ProgressProvider>
            <Navbar />
          </ProgressProvider>
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.queryByRole('link', { name: /Sign In/i })).not.toBeInTheDocument();
  });

  it('renders Clerk-only login without a native password input', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Sign in to MERIT/i)).toBeInTheDocument();
    });
    expect(document.querySelectorAll('input[type="password"]')).toHaveLength(0);
    expect(screen.getByText('Sign-in is not available in this environment.')).toBeInTheDocument();
    expect(screen.getByText('Set VITE_CLERK_PUBLISHABLE_KEY and rebuild.')).toBeInTheDocument();
  });
});
