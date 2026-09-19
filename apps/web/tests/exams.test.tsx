import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
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

  it('shows the coding section after starting the exam', async () => {
    mockGuestFetch();
    renderExams('/exams/foundational-dsa');
    await screen.findByText(/Foundational DSA/);
    fireEvent.click(screen.getByText(/Start timed exam/i));
    expect(await screen.findByText(/Coding questions \(2\)/i)).toBeInTheDocument();
    expect(await screen.findByText('Two Sum')).toBeInTheDocument();
    expect(await screen.findByText('Valid Parentheses')).toBeInTheDocument();
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
});
