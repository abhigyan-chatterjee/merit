import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
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
    window.sessionStorage.clear();
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

  it('gives 2 grace warnings on blur/tab switch before auto-submitting on the 3rd event', async () => {
    stubFetch({ signedIn: true });
    renderExam();

    const start = await screen.findByRole('button', { name: /Start timed exam/i });
    fireEvent.click(start);

    // Event 1: warning 1
    fireEvent.blur(window);
    expect(await screen.findByText(/Warning 1 of 2/i)).toBeInTheDocument();

    // Event 2: warning 2
    fireEvent.blur(window);
    expect(await screen.findByText(/Warning 2 of 2/i)).toBeInTheDocument();

    // Event 3: auto-submit
    fireEvent.blur(window);
    expect(await screen.findByText(/Exam auto-submitted/i)).toBeInTheDocument();
  });

  it('restores active exam countdown and warnings from sessionStorage on refresh', async () => {
    stubFetch({ signedIn: true });
    const endAtMs = Date.now() + 1200 * 1000;
    window.sessionStorage.setItem(
      'merit_exam_foundational-dsa',
      JSON.stringify({ started: true, endAtMs, warnings: 1 })
    );

    renderExam('foundational-dsa', true);

    expect(await screen.findByLabelText(/Time remaining (19:\d\d|20:00)/i)).toBeInTheDocument();
  });

  it('counts a paired blur and visibilitychange as one proctor warning', async () => {
    stubFetch({ signedIn: true });
    renderExam();

    const start = await screen.findByRole('button', { name: /Start timed exam/i });
    fireEvent.click(start);

    const hiddenSpy = vi.spyOn(document, 'hidden', 'get').mockReturnValue(false);
    try {
      fireEvent.blur(window);
      expect(await screen.findByText(/Warning 1 of 2/i)).toBeInTheDocument();

      hiddenSpy.mockReturnValue(true);
      fireEvent(document, new Event('visibilitychange'));

      expect(screen.getByText(/Warning 1 of 2/i)).toBeInTheDocument();
      expect(screen.queryByText(/Warning 2 of 2/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/Exam auto-submitted/i)).not.toBeInTheDocument();
    } finally {
      hiddenSpy.mockRestore();
    }
  });

  it('auto-submits a coding exam, clears its session and locks the coding section', async () => {
    const questions = [
      {
        id: 'q1',
        topic: 'arrays-hashing',
        subtopic: 'maps',
        difficulty: 'Easy',
        prompt: 'First prompt?',
        options: ['a1', 'b1'],
      },
    ];
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = typeof input === 'string' ? input : String(input);
        if (url.includes('/auth/me')) return jsonResponse(PROFILE);
        if (url.includes('/progress/summary')) return jsonResponse(SUMMARY);
        if (url.includes('/attempts/')) {
          return jsonResponse({
            total: 1,
            correct: 0,
            score_pct: 0,
            results: [{ question_id: 'q1', is_correct: false }],
          });
        }
        if (url.includes('/quizzes/generate')) {
          return jsonResponse({ attempt_id: 'a1', questions, total: 1 });
        }
        return jsonResponse({});
      })
    );

    renderExam();
    const start = await screen.findByRole('button', { name: /Start timed exam/i });
    fireEvent.click(start);
    expect(await screen.findByText('First prompt?')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Two Sum/i }));
    expect(await screen.findByText('Coding questions (2)')).toBeInTheDocument();
    expect(window.sessionStorage.getItem('merit_exam_foundational-dsa')).not.toBeNull();

    fireEvent.blur(window);
    fireEvent.blur(window);
    fireEvent.blur(window);

    await waitFor(() => {
      expect(window.sessionStorage.getItem('merit_exam_foundational-dsa')).toBeNull();
    });
    expect(screen.getByText(/Coding is now locked/i)).toBeInTheDocument();
    expect(screen.queryByText('Coding questions (2)')).not.toBeInTheDocument();
  });
});
