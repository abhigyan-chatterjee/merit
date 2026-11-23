import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { StrictMode, useState } from 'react';
import { ExamMcqSection } from '../src/components/ExamMcqSection';
import { ExamCodingSection } from '../src/components/ExamCodingSection';
import { ProgressProvider } from '../src/store/ProgressContext';
import { PROBLEMS } from '../src/data/problems';
import * as apiModule from '../src/utils/api';

function json(body: unknown, ok = true, status = 200) {
  return { ok, status, statusText: '', json: async () => body };
}

const QUESTIONS = [
  { id: 'q1', topic: 'arrays-hashing', subtopic: 'maps', difficulty: 'Easy', prompt: 'First prompt?', options: ['a1', 'b1'] },
  { id: 'q2', topic: 'arrays-hashing', subtopic: 'maps', difficulty: 'Easy', prompt: 'Second prompt?', options: ['a2', 'b2'] },
];

/** Drives the controlled index/answers props the way ExamDetailPage does. */
const McqHarness = ({ onComplete }: { onComplete: (pct: number) => void }) => {
  const [index, setIndex] = useState(0);
  const [, setAnswers] = useState<Record<string, number>>({});
  return (
    <ExamMcqSection
      examId="ex1"
      examTitle="Foundational DSA"
      // Deliberately an inline array: the loader must key off the contents,
      // not the array identity, or it re-fetches and resets the exam.
      topics={['arrays-hashing']}
      questionCount={2}
      difficulty="Easy"
      durationSec={600}
      currentIndex={index}
      onCurrentIndexChange={setIndex}
      onAnswersChange={setAnswers}
      onQuestionIdsChange={() => {}}
      onComplete={onComplete}
    />
  );
};

describe('ExamMcqSection', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('loads and shows the first question with its options', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => json({ attempt_id: 'a1', questions: QUESTIONS, total: 2 })));
    render(<McqHarness onComplete={() => {}} />);

    expect(await screen.findByText('First prompt?')).toBeInTheDocument();
    expect(screen.getByText('Question 1 of 2')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /a1/ })).toBeInTheDocument();
  });

  it('records an answer and updates the running count', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => json({ attempt_id: 'a1', questions: QUESTIONS, total: 2 })));
    render(<McqHarness onComplete={() => {}} />);

    const option = await screen.findByRole('button', { name: /a1/ });
    fireEvent.click(option);
    expect(option).toHaveAttribute('aria-pressed', 'true');
    expect(screen.getByText(/1\/2 answered/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Submit Exam \(1\/2\)/ })).toBeInTheDocument();
  });

  it('navigates between questions', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => json({ attempt_id: 'a1', questions: QUESTIONS, total: 2 })));
    render(<McqHarness onComplete={() => {}} />);

    await screen.findByText('First prompt?');
    expect(screen.getByRole('button', { name: /Previous/i })).toBeDisabled();
    fireEvent.click(screen.getByRole('button', { name: /Next/i }));
    expect(await screen.findByText('Second prompt?')).toBeInTheDocument();
  });

  it('grades on submit and reports the score', async () => {
    const onComplete = vi.fn();
    vi.stubGlobal(
      'fetch',
      vi.fn(async (input: RequestInfo | URL) => {
        const url = typeof input === 'string' ? input : String(input);
        if (url.includes('/attempts/')) {
          return json({
            correct: 1,
            total: 2,
            score_pct: 50,
            results: [
              { question_id: 'q1', is_correct: true },
              { question_id: 'q2', is_correct: false },
            ],
          });
        }
        return json({ attempt_id: 'a1', questions: QUESTIONS, total: 2 });
      }),
    );
    render(<McqHarness onComplete={onComplete} />);

    fireEvent.click(await screen.findByRole('button', { name: /a1/ }));
    fireEvent.click(screen.getByRole('button', { name: /Submit Exam/i }));

    expect(await screen.findByText('Exam Result')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
    expect(screen.getByText('Correct: 1/2')).toBeInTheDocument();
    await waitFor(() => expect(onComplete).toHaveBeenCalledWith(50));
  });

  it('offers a retry when loading fails', async () => {
    const fetchSpy = vi.fn(async () => json({ error: { code: 'X', message: 'boom' } }, false, 500));
    vi.stubGlobal('fetch', fetchSpy);
    render(<McqHarness onComplete={() => {}} />);

    expect(await screen.findByRole('alert')).toHaveTextContent(/Could not load the exam questions/i);
    const callsBefore = fetchSpy.mock.calls.length;
    fireEvent.click(screen.getByRole('button', { name: /Try Again/i }));
    await waitFor(() => expect(fetchSpy.mock.calls.length).toBeGreaterThan(callsBefore));
  });

  it('issues only one generateQuiz request under StrictMode', async () => {
    const fetchSpy = vi.fn(async () => json({ attempt_id: 'a1', questions: QUESTIONS, total: 2 }));
    vi.stubGlobal('fetch', fetchSpy);
    render(
      <StrictMode>
        <McqHarness onComplete={() => {}} />
      </StrictMode>
    );

    expect(await screen.findByText('First prompt?')).toBeInTheDocument();
    expect(fetchSpy).toHaveBeenCalledTimes(1);
  });
});

describe('ExamCodingSection', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('renders the coding questions from the static bundle', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => json({}, false, 401)));
    render(
      <ProgressProvider>
        <MemoryRouter>
          <ExamCodingSection coding={[{ slug: 'two-sum', title: 'Two Sum' }]} onVerdict={() => {}} />
        </MemoryRouter>
      </ProgressProvider>,
    );

    expect(await screen.findByText('Coding questions (1)')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Two Sum' })).toBeInTheDocument();
    // Statement comes from the local PROBLEMS bundle, so it is present offline.
    const twoSum = PROBLEMS.find((p) => p.slug === 'two-sum')!;
    expect(screen.getByText(twoSum.statement)).toBeInTheDocument();
  });

  it('filters to the selected coding question', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => json({}, false, 401)));
    render(
      <ProgressProvider>
        <MemoryRouter>
          <ExamCodingSection
            coding={[
              { slug: 'two-sum', title: 'Two Sum' },
              { slug: 'contains-duplicate', title: 'Contains Duplicate' },
            ]}
            selectedSlug="contains-duplicate"
            onVerdict={() => {}}
          />
        </MemoryRouter>
      </ProgressProvider>,
    );

    expect(await screen.findByText('Coding questions (2)')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Contains Duplicate' })).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Two Sum' })).not.toBeInTheDocument();
  });
});

describe('ExamMcqSection weak-topic breakdown and retry drill', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  const MULTI = [
    { id: 'q1', topic: 'arrays-hashing', subtopic: 'maps', difficulty: 'Easy', prompt: 'First prompt?', options: ['a1', 'b1'] },
    { id: 'q2', topic: 'arrays-hashing', subtopic: 'maps', difficulty: 'Easy', prompt: 'Second prompt?', options: ['a2', 'b2'] },
    { id: 'q3', topic: 'trees', subtopic: 'bst', difficulty: 'Easy', prompt: 'Third prompt?', options: ['a3', 'b3'] },
  ];

  const MultiHarness = ({ onComplete }: { onComplete: (pct: number) => void }) => {
    const [index, setIndex] = useState(0);
    const [, setAnswers] = useState<Record<string, number>>({});
    return (
      <ExamMcqSection
        examId="ex-multi"
        examTitle="Foundational DSA"
        topics={['arrays-hashing', 'trees']}
        questionCount={3}
        difficulty="Easy"
        durationSec={600}
        currentIndex={index}
        onCurrentIndexChange={setIndex}
        onAnswersChange={setAnswers}
        onQuestionIdsChange={() => {}}
        onComplete={onComplete}
      />
    );
  };

  it('shows weak-topic breakdown weakest-first and drills wrong-only without touching official score', async () => {
    const onComplete = vi.fn();
    vi.spyOn(apiModule.quizApi, 'generateQuiz').mockResolvedValue({
      attempt_id: 'a-multi',
      questions: MULTI as never,
      total: 3,
    });
    const submitSpy = vi
      .spyOn(apiModule.quizApi, 'submitQuiz')
      .mockResolvedValueOnce({
        attempt_id: 'a-multi',
        total: 3,
        correct: 1,
        score_pct: 33,
        duration_sec: 10,
        results: [
          { question_id: 'q1', prompt: '', options: [], selected_index: 0, correct_index: 1, is_correct: false, explanation: '' },
          { question_id: 'q2', prompt: '', options: [], selected_index: 0, correct_index: 1, is_correct: false, explanation: '' },
          { question_id: 'q3', prompt: '', options: [], selected_index: 0, correct_index: 0, is_correct: true, explanation: '' },
        ],
      })
      .mockResolvedValueOnce({
        attempt_id: 'drill-1',
        total: 2,
        correct: 2,
        score_pct: 100,
        duration_sec: 5,
        results: [
          { question_id: 'q1', prompt: '', options: [], selected_index: 0, correct_index: 0, is_correct: true, explanation: '' },
          { question_id: 'q2', prompt: '', options: [], selected_index: 0, correct_index: 0, is_correct: true, explanation: '' },
        ],
      });
    vi.spyOn(apiModule.quizApi, 'retryWrong').mockResolvedValue({
      attempt_id: 'drill-1',
      questions: [MULTI[0], MULTI[1]] as never,
      total: 2,
    });

    render(<MultiHarness onComplete={onComplete} />);
    await screen.findByText('First prompt?');

    fireEvent.click(screen.getByRole('button', { name: /a1/ }));
    fireEvent.click(screen.getByRole('button', { name: /Next/i }));
    await screen.findByText('Second prompt?');
    fireEvent.click(screen.getByRole('button', { name: /a2/ }));
    fireEvent.click(screen.getByRole('button', { name: /Next/i }));
    await screen.findByText('Third prompt?');
    fireEvent.click(screen.getByRole('button', { name: /a3/ }));

    fireEvent.click(screen.getByRole('button', { name: /Submit Exam/i }));
    expect(await screen.findByText('Exam Result')).toBeInTheDocument();
    expect(await screen.findByText('Weak-Topic Breakdown')).toBeInTheDocument();
    expect(screen.getByText('0/2 · 0%')).toBeInTheDocument();
    expect(screen.getByText('1/1 · 100%')).toBeInTheDocument();
    expect(screen.getByText('Weak')).toBeInTheDocument();
    const weakSection = screen.getByText('Weak-Topic Breakdown').parentElement!;
    expect(weakSection.textContent!.indexOf('arrays-hashing')).toBeLessThan(weakSection.textContent!.indexOf('trees'));
    await waitFor(() => expect(onComplete).toHaveBeenCalledTimes(1));
    expect(onComplete).toHaveBeenCalledWith(33);

    fireEvent.click(screen.getByRole('button', { name: /Retry Wrong Only \(2\)/ }));
    expect(await screen.findByText('Practice Drill — Missed Questions')).toBeInTheDocument();
    expect(screen.getByText(/Drill Question 1 of 2/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Back to Exam Result/ })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /a1/ }));
    fireEvent.click(screen.getByRole('button', { name: /Next/i }));
    await screen.findByText('Second prompt?');
    fireEvent.click(screen.getByRole('button', { name: /a2/ }));
    fireEvent.click(screen.getByRole('button', { name: /Submit Drill/i }));
    expect(await screen.findByText(/Drill score: 2\/2/)).toBeInTheDocument();
    expect(submitSpy).toHaveBeenCalledTimes(2);
    expect(onComplete).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole('button', { name: /Back to Exam Result/ }));
    expect(await screen.findByText('Exam Result')).toBeInTheDocument();
    expect(screen.getByText('Weak-Topic Breakdown')).toBeInTheDocument();
  });

  it('falls back to local missed questions when retryWrong fails', async () => {
    const onComplete = vi.fn();
    vi.spyOn(apiModule.quizApi, 'generateQuiz').mockResolvedValue({
      attempt_id: 'a-fallback',
      questions: MULTI.slice(0, 2) as never,
      total: 2,
    });
    vi.spyOn(apiModule.quizApi, 'submitQuiz').mockResolvedValue({
      attempt_id: 'a-fallback',
      total: 2,
      correct: 1,
      score_pct: 50,
      duration_sec: 8,
      results: [
        { question_id: 'q1', prompt: '', options: [], selected_index: 0, correct_index: 0, is_correct: true, explanation: '' },
        { question_id: 'q2', prompt: '', options: [], selected_index: 0, correct_index: 1, is_correct: false, explanation: '' },
      ],
    });
    vi.spyOn(apiModule.quizApi, 'retryWrong').mockRejectedValue(new Error('no server drill'));

    render(<MultiHarness onComplete={onComplete} />);
    await screen.findByText('First prompt?');
    fireEvent.click(screen.getByRole('button', { name: /a1/ }));
    fireEvent.click(screen.getByRole('button', { name: /Submit Exam/i }));

    expect(await screen.findByText('Exam Result')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Retry Wrong Only \(1\)/ }));
    expect(await screen.findByText('Practice Drill — Missed Questions')).toBeInTheDocument();
    expect(onComplete).toHaveBeenCalledTimes(1);
  });
});
