import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ProfilePage } from '../src/pages/ProfilePage';
import { AuthProvider } from '../src/store/AuthContext';
import { ProgressProvider } from '../src/store/ProgressContext';

const PROFILE = {
  id: 'u1',
  email: 'student@merit.org',
  display_name: 'Student One',
  displayName: 'Student One',
  role: 'user',
  created_at: '2026-01-01T00:00:00Z',
  last_login_at: null,
};

const SUMMARY = {
  has_imported_local: true,
  progress: {},
  notes: {},
  activity_days: {},
  visited_visualizers: [],
  bookmarks: [],
  current_streak: 0,
  solved_count: 0,
  daily_goal: null,
};

function stubFetch() {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : String(input);
      const body = url.includes('/auth/me')
        ? PROFILE
        : url.includes('/progress/summary')
          ? SUMMARY
          : {};
      return { ok: true, status: 200, statusText: '', json: async () => body };
    }),
  );
}

function renderProfile(path = '/profile') {
  return render(
    <AuthProvider>
      <ProgressProvider>
        <MemoryRouter initialEntries={[path]}>
          <ProfilePage />
        </MemoryRouter>
      </ProgressProvider>
    </AuthProvider>,
  );
}

describe('ProfilePage', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('shows the signed-in account and the profile tab by default', async () => {
    stubFetch();
    renderProfile();
    expect(await screen.findByRole('heading', { name: 'Student One' })).toBeInTheDocument();
    expect(screen.getByLabelText('Display name')).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: /Breadcrumb/i })).toBeInTheDocument();
  });

  it('opens the language tab from the ?tab= query', async () => {
    stubFetch();
    renderProfile('/profile?tab=language');
    expect(await screen.findByText(/Preferred language/i)).toBeInTheDocument();
  });

  it('switches tabs', async () => {
    stubFetch();
    renderProfile();
    await screen.findByRole('heading', { name: 'Student One' });

    fireEvent.click(screen.getByRole('button', { name: /Tutor/i }));
    expect(screen.getByText(/Tutor settings/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Danger/i }));
    expect(screen.getByText(/Delete account/i)).toBeInTheDocument();
  });
});
