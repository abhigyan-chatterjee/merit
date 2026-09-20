import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../src/store/AuthContext';
import { ProgressProvider } from '../src/store/ProgressContext';
import { ExamsPage } from '../src/pages/ExamsPage';
import { ExamDetailPage } from '../src/pages/ExamDetailPage';
import { QuizEngine } from '../src/components/QuizEngine';
import { ExamCodingSection } from '../src/components/ExamCodingSection';
import { Routes, Route } from 'react-router-dom';
import { TARGETED_EXAMS } from '../src/data/exams';
import * as apiModule from '../src/utils/api';

function renderExams(initialEntry = '/exams') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <AuthProvider>
        <ProgressProvider>
          <Routes>
            <Route path="/exams" element={<ExamsPage />} />
            <Route path="/exams/:id" element={<ExamDetailPage />} />
          </Routes>
        </ProgressProvider>
      </AuthProvider>
    </MemoryRouter>
  );
}

function renderEngine(ui: React.ReactElement) {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <ProgressProvider>{ui}</ProgressProvider>
      </AuthProvider>
    </MemoryRouter>
  );
}

describe('Exams catalog', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  function mockGuestFetch() {
    vi.spyOn(global, 'fetch').mockImplementation(async (url) => {
      const u = String(url);
      if (u.includes('/auth/me') || u.includes('/auth/refresh')) {
        return new Response(
          JSON.stringify({ error: { code: 'UNAUTHORIZED', message: 'Not logged in' } }),
          { status: 401, headers: { 'Content-Type': 'application/json' } }
        );
      }
      return new Response(JSON.stringify({}), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    });
  }

  it('lists every targeted exam with MCQ + coding counts and duration', async () => {
    mockGuestFetch();
    renderExams();
    for (const exam of TARGETED_EXAMS) {
      expect(await screen.findByText(exam.title)).toBeInTheDocument();
    }
    expect(screen.getByText('Foundational DSA')).toBeInTheDocument();
    expect(screen.getByText('Aptitude')).toBeInTheDocument();
    expect(screen.getByText('Full Placement Mock')).toBeInTheDocument();
    // collapsed single meta line: "20 MCQs · 2 coding · 45 min"; aptitude is MCQ-only
    expect(screen.getAllByText(/20 MCQs · 2 coding/i).length).toBeGreaterThanOrEqual(5);
    expect(screen.getAllByText(/20 MCQs/i).length).toBeGreaterThanOrEqual(6);
  });

  it('routes an exam card to its timed detail page', async () => {
    mockGuestFetch();
    renderExams();
    await screen.findByText('Intermediate DSA');
    fireEvent.click(screen.getAllByText('Start exam')[0]);
    expect(await screen.findByText(/Ready when you are/i)).toBeInTheDocument();
    expect(await screen.findAllByText(/coding questions/i)).not.toHaveLength(0);
  });

  it('shows no coding section for the MCQ-only aptitude exam', async () => {
    // Authed so the MCQ engine actually loads; aptitude must still render zero coding items.
    vi.spyOn(apiModule.authApi, 'getMe').mockResolvedValue({
      id: 'usr-apt',
      email: 'apt@test.com',
      display_name: 'Apt User',
      displayName: 'Apt User',
      role: 'student',
      created_at: '2026-09-01T00:00:00Z',
      last_login_at: null,
    });
    vi.spyOn(apiModule.quizApi, 'generateQuiz').mockResolvedValue({
      attempt_id: 'att-apt-1',
      questions: [
        {
          id: 'q-apt-1',
          topic: 'aptitude',
          subtopic: null,
          difficulty: 'Easy',
          prompt: 'Aptitude sample question?',
          options: ['A', 'B', 'C', 'D'],
        },
      ],
      total: 1,
    });
    renderExams('/exams/aptitude');
    await screen.findByText(/Aptitude/);
    expect(screen.getByText(/20 MCQs · 30 min/i)).toBeInTheDocument();
    expect(screen.queryByText(/2 coding/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByText(/Start timed exam/i));
    expect(
      await screen.findByText((_content, el) => {
        if (!el || el.tagName !== 'H3') return false;
        return (el.textContent ?? '').includes('Aptitude sample question?');
      })
    ).toBeInTheDocument();
    expect(screen.queryByText(/Coding questions/i)).not.toBeInTheDocument();
  });

  it('shows the coding navigator item after starting the exam', async () => {
    vi.spyOn(apiModule.authApi, 'getMe').mockResolvedValue({
      id: 'usr-coding',
      email: 'coding@test.com',
      display_name: 'Coder',
      displayName: 'Coder',
      role: 'student',
      created_at: '2026-09-01T00:00:00Z',
      last_login_at: null,
    });
    vi.spyOn(apiModule.quizApi, 'generateQuiz').mockResolvedValue({
      attempt_id: 'att-coding',
      questions: Array.from({ length: 20 }, (_, index) => ({
        id: `q-${index + 1}`,
        topic: 'arrays-hashing',
        subtopic: null,
        difficulty: 'Easy',
        prompt: `Question ${index + 1}?`,
        options: ['A', 'B', 'C', 'D'],
      })),
      total: 20,
    });
    renderExams('/exams/foundational-dsa');
    await screen.findByText(/Foundational DSA/);
    fireEvent.click(screen.getByText(/Start timed exam/i));
    expect((await screen.findAllByText(/Coding \(2\)/i)).length).toBeGreaterThan(0);
    expect(screen.getByRole('button', { name: /Two Sum/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Valid Parentheses/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Two Sum/i }));
    expect(await screen.findByText(/Given an array of integers/i)).toBeInTheDocument();
  });

  it('shows sign-in prompt for guests instead of Start timed exam', async () => {
    mockGuestFetch();
    renderExams('/exams/foundational-dsa');
    await screen.findByText(/Foundational DSA/);
    expect(screen.queryByText(/Start timed exam/i)).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Sign in to start exam/i })).toBeInTheDocument();
  });

  it('navigates to an MCQ and preserves its answer', async () => {
    vi.spyOn(apiModule.authApi, 'getMe').mockResolvedValue({
      id: 'usr-navigator',
      email: 'navigator@test.com',
      display_name: 'Navigator',
      displayName: 'Navigator',
      role: 'student',
      created_at: '2026-09-01T00:00:00Z',
      last_login_at: null,
    });
    vi.spyOn(apiModule.quizApi, 'generateQuiz').mockResolvedValue({
      attempt_id: 'att-navigator-1',
      questions: Array.from({ length: 20 }, (_, index) => ({
        id: `q-${index + 1}`,
        topic: 'arrays-hashing',
        subtopic: null,
        difficulty: 'Easy',
        prompt: `Navigator question ${index + 1}?`,
        options: ['A', 'B', 'C', 'D'],
      })),
      total: 20,
    });
    renderExams('/exams/aptitude');
    fireEvent.click(await screen.findByText(/Start timed exam/i));
    expect(await screen.findByText(/Navigator question 1/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Question 3/i }));
    expect(await screen.findByText(/Navigator question 3/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /^AA$/i }));
    fireEvent.click(screen.getByRole('button', { name: /^Question 1unanswered$/i }));
    expect(await screen.findByText(/Navigator question 1/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /^Question 3answered$/i }));
    expect(await screen.findByRole('button', { name: /^AA$/i })).toHaveClass('border-mint');
    expect(screen.getByLabelText('answered')).toBeInTheDocument();
  });

  it('samples a targeted exam topic set from the server bank', async () => {
    // Deterministic authenticated session: every getMe() resolves to the
    // student so the engine samples from the server exam bank. Renders the
    // engine directly (same pattern as the passing quizEngine server test)
    // to avoid depending on the detail page's Start-gate timing.
    vi.spyOn(apiModule.authApi, 'getMe').mockResolvedValue({
      id: 'usr-exam',
      email: 'exam@test.com',
      display_name: 'Exam User',
      displayName: 'Exam User',
      role: 'student',
      created_at: '2026-09-01T00:00:00Z',
      last_login_at: null,
    });
    const genSpy = vi.spyOn(apiModule.quizApi, 'generateQuiz').mockResolvedValue({
      attempt_id: 'att-exam-1',
      questions: [
        {
          id: 'q-dp-1',
          topic: 'dynamic-programming',
          subtopic: null,
          difficulty: 'Medium',
          prompt: 'Exam DP question?',
          options: ['A', 'B', 'C', 'D'],
        },
      ],
      total: 1,
    });

    renderEngine(
      <QuizEngine
        topicTitle="Dynamic Programming"
        topicId="mixed"
        examTopics={['dynamic-programming']}
        examCount={10}
        isMock
        durationLimitSec={1200}
      />
    );

    expect(
      await screen.findByText((_content, el) => {
        if (!el || el.tagName !== 'H3') return false;
        return (el.textContent ?? '').replace(/\s+/g, ' ').includes('Exam DP question?');
      })
    ).toBeInTheDocument();
    expect(genSpy).toHaveBeenCalledWith(['dynamic-programming'], 10, undefined, true, 1200, undefined);
  });

  it('shows the empty-bank state to guests without hitting the server', async () => {
    mockGuestFetch();
    const genSpy = vi.spyOn(apiModule.quizApi, 'generateQuiz');

    renderEngine(
      <QuizEngine
        topicTitle="Dynamic Programming"
        topicId="mixed"
        examTopics={['dynamic-programming']}
        examCount={10}
        isMock
        durationLimitSec={1200}
      />
    );

    expect(await screen.findAllByText(/No Questions Available/i)).not.toHaveLength(0);
    expect(screen.getByText(/Try Again/i)).toBeInTheDocument();
    expect(genSpy).not.toHaveBeenCalled();
  });

  it('exam coding item renders statement + examples inline', async () => {
    renderEngine(<ExamCodingSection coding={[{ slug: 'two-sum', title: 'Two Sum' }]} onVerdict={() => {}} />);
    // Full statement visible inline without clicking the "Open full statement" link.
    expect(await screen.findByText(/Given an array of integers/i)).toBeInTheDocument();
    expect(await screen.findByText(/Example 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Open full statement/i)).toBeInTheDocument();
  });

  it('marks the navigator item Attempted after a non-AC exam coding submit', async () => {
    const { judgeApi } = await import('../src/utils/api');
    vi.spyOn(judgeApi, 'submit').mockResolvedValue({
      id: 'sub-wa-1',
      problem_slug: 'two-sum',
      language: 'javascript',
      verdict: 'WA',
      runtime_ms: 6.1,
      test_results: [
        { label: 'Case 1', passed: false, input: [[2, 7], 9], expected: [0, 1], actual: [0, 0], runtime_ms: 2.0, error: null },
      ],
      created_at: '2026-09-20T00:00:00Z',
    });
    renderEngine(
      <ExamCodingSection coding={[{ slug: 'two-sum', title: 'Two Sum' }]} onVerdict={() => {}} />
    );
    await screen.findByText(/Given an array of integers/i);
    fireEvent.click(screen.getByRole('button', { name: /^Submit$/i }));
    expect(await screen.findByText(/^Attempted$/i)).toBeInTheDocument();
  });

  it('auto-submits the timed mock when the countdown reaches zero', async () => {
    const { progressApi } = await import('../src/utils/api');
    vi.spyOn(progressApi, 'getSummary').mockResolvedValue({
      solved_count: 0,
      doing_count: 0,
      total_problems: 140,
      current_streak: 0,
      activity_days: {},
      progress: {},
      notes: {},
      bookmarks: [],
      visited_visualizers: [],
      has_imported_local: true,
      quiz_scores: {},
      weakest_topics: [],
      revision_due: [],
      preferred_language: 'javascript',
      daily_goal: null,
    });
    vi.spyOn(apiModule.authApi, 'getMe').mockResolvedValue({
      id: 'usr-auto',
      email: 'auto@test.com',
      display_name: 'Auto User',
      displayName: 'Auto User',
      role: 'student',
      created_at: '2026-09-01T00:00:00Z',
      last_login_at: null,
    });
    vi.spyOn(apiModule.quizApi, 'generateQuiz').mockResolvedValue({
      attempt_id: 'att-auto-1',
      questions: [
        {
          id: 'q-auto-1',
          topic: 'aptitude',
          subtopic: null,
          difficulty: 'Easy',
          prompt: 'Auto-submit probe question?',
          options: ['A', 'B', 'C', 'D'],
        },
      ],
      total: 1,
      duration_sec: 2,
    });
    const submitSpy = vi.spyOn(apiModule.quizApi, 'submitQuiz').mockResolvedValue({
      attempt_id: 'att-auto-1',
      total: 1,
      correct: 0,
      score_pct: 0,
      duration_sec: 2,
      results: [
        {
          question_id: 'q-auto-1',
          prompt: 'Auto-submit probe question?',
          options: ['A', 'B', 'C', 'D'],
          selected_index: null,
          correct_index: 0,
          is_correct: false,
          explanation: 'Unanswered counts as wrong.',
        },
      ],
    });

    renderEngine(
      <QuizEngine
        topicTitle="Aptitude Mock"
        topicId="mixed"
        examTopics={['aptitude']}
        examCount={1}
        isMock
        durationLimitSec={2}
      />
    );

    expect(await screen.findByText(/Auto-submit probe question/i)).toBeInTheDocument();
    await screen.findByText(/Remaining:/i);
    await waitFor(
      () => {
        expect(submitSpy).toHaveBeenCalledWith('att-auto-1', expect.any(Number), {});
      },
      { timeout: 8000 },
    );
    expect(await screen.findByText(/Score: 0%/i)).toBeInTheDocument();
  }, 15000);

  it('does not render AiTutor inside the exam coding section', async () => {
    renderEngine(<ExamCodingSection coding={[{ slug: 'two-sum', title: 'Two Sum' }]} onVerdict={() => {}} />);
    await screen.findByText(/Given an array of integers/i);
    expect(screen.queryByRole('button', { name: /ask the tutor/i })).not.toBeInTheDocument();
  });
});
