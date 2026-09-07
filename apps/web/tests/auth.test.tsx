import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider, useAuth } from '../src/store/AuthContext';
import { LoginPage } from '../src/pages/LoginPage';
import { RegisterPage } from '../src/pages/RegisterPage';
import { Navbar } from '../src/components/Navbar';
import { ProgressProvider } from '../src/store/ProgressContext';

const TestAuthConsumer = () => {
  const { user, login, logout, isLoading } = useAuth();
  if (isLoading) return <div>Loading...</div>;
  return (
    <div>
      <span data-testid="user-email">{user ? user.email : 'guest'}</span>
      <button onClick={() => login('test@algovista.org', 'ValidPass123!')}>Login</button>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
};

describe('Auth Integration and UI', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
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
      expect(screen.getByTestId('user-email')).toHaveTextContent('test@algovista.org');
    });
  });

  it('validates password length on RegisterPage', async () => {
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

    const nameInput = screen.getByLabelText(/Display Name/i);
    const emailInput = screen.getByLabelText(/Email Address/i);
    const passInput = screen.getByLabelText(/^Password/i);
    const confirmInput = screen.getByLabelText(/Confirm Password/i);
    const submitBtn = screen.getByRole('button', { name: /Create Account/i });

    fireEvent.change(nameInput, { target: { value: 'Ada' } });
    fireEvent.change(emailInput, { target: { value: 'ada@example.com' } });
    fireEvent.change(passInput, { target: { value: 'short' } });
    fireEvent.change(confirmInput, { target: { value: 'short' } });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Password must be at least 10 characters long.');
    });
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

  it('validates empty inputs on LoginPage', async () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <LoginPage />
        </AuthProvider>
      </MemoryRouter>
    );

    const submitBtn = screen.getByRole('button', { name: /Sign In/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Please fill in both email and password.');
    });
  });
});
