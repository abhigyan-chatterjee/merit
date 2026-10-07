import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { useState } from 'react';
import { ExamMcqSection } from '../src/components/ExamMcqSection';
import { ExamCodingSection } from '../src/components/ExamCodingSection';
import { ProgressProvider } from '../src/store/ProgressContext';
import { PROBLEMS } from '../src/data/problems';

function json(body: unknown, ok = true, status = 200) {
  return { ok, status, statusText: '', json: async () => body };
}

// Module-level so the identity is stable across renders: ExamMcqSection lists
// `topics` in loadQuestions' deps, so an inline array would re-fire the loader.
const TOPICS = ['arrays-hashing'];

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
      topics={TOPICS}
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
