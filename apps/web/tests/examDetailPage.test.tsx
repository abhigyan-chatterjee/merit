import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ExamDetailPage } from '../src/pages/ExamDetailPage';
import { AuthProvider } from '../src/store/AuthContext';
import { ProgressProvider } from '../src/store/ProgressContext';

const PROFILE = {
  id: 'u1',
  email: 'student@merit.org',
  display_name: 'Student',
  displayName: 'Student',
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

function jsonResponse(body: unknown, ok = true, status = 200) {
  return { ok, status, statusText: '', json: async () => body };
}

/** fetch stub: the exam page and its child sections probe several endpoints. */
function stubFetch({ signedIn }: { signedIn: boolean }) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : String(input);
      if (url.includes('/auth/me')) {
        return signedIn
          ? jsonResponse(PROFILE)
          : jsonResponse({ error: { code: 'UNAUTHENTICATED', message: 'no session' } }, false, 401);
      }
      if (url.includes('/progress/summary')) return jsonResponse(SUMMARY);
      // Quiz/coding sections: no questions available is a handled state.
      return jsonResponse({ error: { code: 'NO_QUESTIONS_FOR_TOPICS', message: 'none' } }, false, 404);
    }),
  );
}

function renderExam(id = 'foundational-dsa', signedIn = false) {
  return render(
    <AuthProvider>
      <ProgressProvider>
        <MemoryRouter initialEntries={[`/exams/${id}`]}>
          <Routes>
            <Route path="/exams/:id" element={<ExamDetailPage />} />
          </Routes>
        </MemoryRouter>
      </ProgressProvider>
    </AuthProvider>,
  );
}

describe('ExamDetailPage', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders not-found for an unknown exam id', () => {
    stubFetch({ signedIn: false });
    renderExam('no-such-exam');
    expect(screen.getByText(/Exam Not Found/i)).toBeInTheDocument();
  });

  it('shows the exam composition from the catalog', () => {
    stubFetch({ signedIn: false });
    renderExam();
    expect(screen.getByRole('heading', { name: /Foundational DSA/i })).toBeInTheDocument();
    // The composition is stated in both the header and the start panel.
    expect(screen.getAllByText(/20 MCQs/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/2 coding/).length).toBeGreaterThan(0);
  });

  it('asks a guest to sign in instead of starting', async () => {
    stubFetch({ signedIn: false });
    renderExam();
    const link = await screen.findByRole('link', { name: /Sign in to start exam/i });
    expect(link).toHaveAttribute('href', expect.stringContaining('/login?next='));
  });

  it('starts the timed exam for a signed-in user and shows the countdown', async () => {
    stubFetch({ signedIn: true });
    renderExam();

    const start = await screen.findByRole('button', { name: /Start timed exam/i });
    fireEvent.click(start);

    // The countdown appears with an accessible label naming the time left.
    expect(await screen.findByLabelText(/Time remaining \d+:\d\d/i)).toBeInTheDocument();
  });
});
