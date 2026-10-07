import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { UserDropdown } from '../src/components/UserDropdown';
import { AuthProvider, useAuth } from '../src/store/AuthContext';

function makeProfile(role: string) {
  return {
    id: 'u1',
    email: 'student@merit.org',
    display_name: 'Student One',
    displayName: 'Student One',
    role,
    created_at: '2026-01-01T00:00:00Z',
    last_login_at: null,
  };
}

function stubFetch(profile: ReturnType<typeof makeProfile>) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : String(input);
      const body = url.includes('/auth/me') ? profile : {};
      return { ok: true, status: 200, statusText: '', json: async () => body };
    }),
  );
}

/** Mirrors the Navbar: only rendered while a user is signed in. */
const Shell: React.FC = () => {
  const { user } = useAuth();
  return user ? <UserDropdown /> : <span>signed out</span>;
};

function renderShell() {
  return render(
    <AuthProvider>
      <MemoryRouter>
        <Shell />
      </MemoryRouter>
    </AuthProvider>,
  );
}

describe('UserDropdown', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('shows the signed-in identity on the toggle', async () => {
    stubFetch(makeProfile('user'));
    renderShell();
    const toggle = await screen.findByRole('button', { name: 'Account menu' });
    expect(toggle).toHaveTextContent('Student One');
    expect(toggle).toHaveAttribute('title', expect.stringContaining('student@merit.org'));
  });

  it('opens a menu with account actions', async () => {
    stubFetch(makeProfile('user'));
    renderShell();
    fireEvent.click(await screen.findByRole('button', { name: 'Account menu' }));

    expect(screen.getByText('student@merit.org')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Profile & settings/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Delete account/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign out/i })).toBeInTheDocument();
  });

  it('hides the admin console for non-admins and shows it for admins', async () => {
    stubFetch(makeProfile('user'));
    const first = renderShell();
    fireEvent.click(await screen.findByRole('button', { name: 'Account menu' }));
    expect(screen.queryByRole('button', { name: /Admin Console/i })).not.toBeInTheDocument();
    first.unmount();

    stubFetch(makeProfile('admin'));
    renderShell();
    fireEvent.click(await screen.findByRole('button', { name: 'Account menu' }));
    expect(screen.getByRole('button', { name: /Admin Console/i })).toBeInTheDocument();
  });

  it('signs out from the menu', async () => {
    stubFetch(makeProfile('user'));
    renderShell();
    fireEvent.click(await screen.findByRole('button', { name: 'Account menu' }));
    fireEvent.click(screen.getByRole('button', { name: /Sign out/i }));

    expect(await screen.findByText('signed out')).toBeInTheDocument();
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: 'Account menu' })).not.toBeInTheDocument(),
    );
  });
});
