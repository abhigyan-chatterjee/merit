import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';

// Clerk's React widgets need a live Clerk instance; these tests assert the
// gating logic around them instead. `clerkState` is mutated per test to move
// between "signed in to Clerk" and "password account with no Clerk session",
// which is the state every seeded Merit account is in.
const mocks = vi.hoisted(() => ({
  clerkState: { isLoaded: true, isSignedIn: false },
  changeEmail: vi.fn(),
  changePassword: vi.fn(),
  profile: {
    id: 'u1',
    email: 'student@merit.org',
    display_name: 'Student One',
    displayName: 'Student One',
    role: 'user',
    created_at: '2026-01-01T00:00:00Z',
    last_login_at: null as string | null,
  },
}));

vi.mock('@clerk/clerk-react', () => ({
  ClerkProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  UserProfile: () => <div data-testid="clerk-user-profile">Clerk embedded profile</div>,
  useAuth: () => mocks.clerkState,
}));

vi.mock('../src/store/AuthContext', () => ({
  useAuth: () => ({
    user: mocks.profile,
    updateProfile: vi.fn(),
    deleteAccount: vi.fn(),
    changeEmail: mocks.changeEmail,
    changePassword: mocks.changePassword,
  }),
}));

function stubFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : String(input);
      const body = url.includes('/auth/me') ? mocks.profile : {};
      return { ok: true, status: 200, statusText: '', json: async () => body };
    }),
  );
}

async function renderProfile() {
  const { ProfilePage } = await import('../src/pages/ProfilePage');
  return render(
    <MemoryRouter initialEntries={['/profile']}>
      <ProfilePage />
    </MemoryRouter>,
  );
}

describe('ProfilePage account security', () => {
  beforeEach(() => {
    vi.stubEnv('VITE_CLERK_PUBLISHABLE_KEY', 'pk_test_profile');
    vi.resetModules();
    mocks.clerkState = { isLoaded: true, isSignedIn: false };
    mocks.changeEmail.mockReset();
    mocks.changePassword.mockReset();
    window.localStorage.clear();
    stubFetch();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.unstubAllEnvs();
  });

  it('renders the working email and password forms when there is no Clerk session', async () => {
    await renderProfile();

    expect(await screen.findByRole('heading', { name: 'Account security' })).toBeInTheDocument();
    expect(screen.getByLabelText('New email')).toBeInTheDocument();
    expect(screen.getByLabelText('Current password')).toBeInTheDocument();
    expect(screen.getByLabelText('New password')).toBeInTheDocument();
    expect(screen.queryByTestId('clerk-user-profile')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Link Social Account/i })).not.toBeInTheDocument();
  });

  it('renders the embedded Clerk profile once Clerk reports a signed-in user', async () => {
    mocks.clerkState = { isLoaded: true, isSignedIn: true };
    await renderProfile();

    expect(await screen.findByTestId('clerk-user-profile')).toBeInTheDocument();
    // The native forms would be a second, conflicting place to change the same
    // credentials, so they stay out of the Clerk-backed view.
    expect(screen.queryByLabelText('New email')).not.toBeInTheDocument();
  });

  it('submits an email change through the auth context', async () => {
    mocks.changeEmail.mockResolvedValue(undefined);
    await renderProfile();

    fireEvent.change(await screen.findByLabelText('New email'), {
      target: { value: 'moved@merit.org' },
    });
    fireEvent.change(screen.getByLabelText('Account password'), {
      target: { value: 'current-secret' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Update email/i }));

    await waitFor(() => {
      expect(mocks.changeEmail).toHaveBeenCalledWith('moved@merit.org', 'current-secret');
    });
  });

  it('rejects a password change whose confirmation does not match', async () => {
    await renderProfile();

    fireEvent.change(await screen.findByLabelText('Current password'), {
      target: { value: 'current-secret' },
    });
    fireEvent.change(screen.getByLabelText('New password'), {
      target: { value: 'a-long-enough-password' },
    });
    fireEvent.change(screen.getByLabelText('Confirm new password'), {
      target: { value: 'a-different-password' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Update password/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/do not match/i);
    expect(mocks.changePassword).not.toHaveBeenCalled();
  });

  it('keeps the native forms when Clerk is not configured at all', async () => {
    vi.stubEnv('VITE_CLERK_PUBLISHABLE_KEY', '');
    vi.resetModules();
    await renderProfile();

    expect(await screen.findByRole('heading', { name: 'Account security' })).toBeInTheDocument();
    expect(screen.getByLabelText('New email')).toBeInTheDocument();
    expect(screen.queryByTestId('clerk-user-profile')).not.toBeInTheDocument();
  });
});
