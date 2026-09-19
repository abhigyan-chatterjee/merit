import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { QuizEngine } from '../src/components/QuizEngine';
import { QUIZ_TOPICS, QUIZZES } from '../src/data/quizzes';
import { ProgressProvider } from '../src/store/ProgressContext';
import { AuthProvider } from '../src/store/AuthContext';
import * as apiModule from '../src/utils/api';

const sampleQuestions = [
  {
    id: 'test-q1',
    question: 'What is the time complexity of binary search?',
    options: ['O(log n)', 'O(n)', 'O(n^2)', 'O(1)'],
    correctIndex: 0,
    explanation: 'Binary search repeatedly halves the search space.',
  },
  {
    id: 'test-q2',
    question: 'Which data structure follows LIFO?',
    options: ['Queue', 'Stack', 'Heap', 'Tree'],
    correctIndex: 1,
    explanation: 'Stack follows Last-In First-Out.',
  },
];

describe('QuizEngine Component', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it.each(QUIZ_TOPICS)('renders 10 guest questions for $id', async ({ id, title }) => {
    render(
      <AuthProvider>
        <ProgressProvider>
          <QuizEngine
            topicTitle={title}
            topicId={id}
            questions={QUIZZES[id]}
            perQuestionSec={null}
          />
        </ProgressProvider>
      </AuthProvider>
    );

    expect(await screen.findByText(/Question 1 of 10/i)).toBeInTheDocument();
    expect(QUIZZES[id]).toHaveLength(10);
  });

  it('renders guest quiz with local questions correctly', async () => {
    render(
      <AuthProvider>
        <ProgressProvider>
          <QuizEngine
            topicTitle="Arrays & Pointers"
            topicId="arrays-hashing"
            questions={sampleQuestions}
            perQuestionSec={null}
          />
        </ProgressProvider>
      </AuthProvider>
    );

    expect(await screen.findByText(/Arrays & Pointers Mastery Quiz/i)).toBeInTheDocument();
    expect(screen.getByText(/1. What is the time complexity of binary search?/i)).toBeInTheDocument();
    expect(screen.getByText('O(log n)')).toBeInTheDocument();
    expect(screen.getByText('O(n)')).toBeInTheDocument();
  });

  it('allows answering, navigating, and submitting with local grading for guests', async () => {
    const onComplete = vi.fn();

    render(
      <AuthProvider>
        <ProgressProvider>
          <QuizEngine
            topicTitle="Algorithms"
            topicId="arrays-hashing"
            questions={sampleQuestions}
            perQuestionSec={null}
            onComplete={onComplete}
          />
        </ProgressProvider>
      </AuthProvider>
    );

    // Answer question 1 correctly (O(log n) -> index 0)
    const opt0 = await screen.findByText('O(log n)');
    fireEvent.click(opt0);

    // Navigate to next question
    const nextBtn = screen.getByText(/Next →/i);
    fireEvent.click(nextBtn);

    expect(screen.getByText(/2. Which data structure follows LIFO\?/i)).toBeInTheDocument();

    // Answer question 2 incorrectly (Queue -> index 0 instead of Stack -> 1)
    const optQueue = screen.getByText('Queue');
    fireEvent.click(optQueue);

    // Submit quiz
    const submitBtn = screen.getByText(/Submit Quiz/i);
    fireEvent.click(submitBtn);

    // Score should be 50%
    await waitFor(() => {
      expect(screen.getByText(/Score: 50%/i)).toBeInTheDocument();
    });
    expect(onComplete).toHaveBeenCalledWith(50);

    // Explanation should appear
    expect(screen.getByText(/Algorithmic Explanation:/i)).toBeInTheDocument();
    expect(screen.getByText(/Stack follows Last-In First-Out./i)).toBeInTheDocument();

    // "Retry Wrong Only" button should be visible since 1 question was incorrect
    const retryWrongBtn = screen.getByText(/Retry Wrong Only \(1\)/i);
    expect(retryWrongBtn).toBeInTheDocument();

    // Click retry wrong only
    fireEvent.click(retryWrongBtn);

    // Now active questions should only have question 2
    expect(screen.getByText(/Question 1 of 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Which data structure follows LIFO\?/i)).toBeInTheDocument();
  });

  it('uses server quiz API when authenticated and displays verified bank badge', async () => {
    // Deterministic authenticated session from the start: every getMe()
    // resolves to the student, so both the provider and the engine agree.
    const student = {
      id: 'usr-1',
      email: 'student@test.com',
      display_name: 'Test Student',
      displayName: 'Test Student',
      role: 'student',
      created_at: '2026-09-01T00:00:00Z',
      last_login_at: null,
    };
    vi.spyOn(apiModule.authApi, 'getMe').mockResolvedValue(student);

    // Mock quiz generation
    vi.spyOn(apiModule.quizApi, 'generateQuiz').mockResolvedValue({
      attempt_id: 'att-123',
      questions: [
        {
          id: 'q-server-1',
          topic: 'trees',
          subtopic: 'bst',
          difficulty: 'easy',
          prompt: 'Server question: What is BST inorder order?',
          options: ['Ascending', 'Descending', 'Random', 'None'],
        },
      ],
      total: 1,
    });

    // Mock quiz submission
    vi.spyOn(apiModule.quizApi, 'submitQuiz').mockResolvedValue({
      attempt_id: 'att-123',
      total: 1,
      correct: 1,
      score_pct: 100,
      duration_sec: 12,
      results: [
        {
          question_id: 'q-server-1',
          prompt: 'Server question: What is BST inorder order?',
          options: ['Ascending', 'Descending', 'Random', 'None'],
          selected_index: 0,
          correct_index: 0,
          is_correct: true,
          explanation: 'Inorder traversal on BST visits elements in strictly ascending order.',
        },
      ],
    });

    render(
      <AuthProvider>
        <ProgressProvider>
          <QuizEngine
            topicTitle="Trees & BST"
            topicId="trees"
            questions={sampleQuestions}
            perQuestionSec={null}
          />
        </ProgressProvider>
      </AuthProvider>
    );

    // Verified bank badge appears
    expect(await screen.findByText(/Verified Bank/i)).toBeInTheDocument();
    expect(screen.getByText(/Server question: What is BST inorder order\?/i)).toBeInTheDocument();

    // Select option 0
    fireEvent.click(screen.getByText('Ascending'));

    // Submit
    fireEvent.click(screen.getByText(/Submit Quiz/i));

    // Verify submission result
    await waitFor(() => {
      expect(screen.getByText(/Score: 100%/i)).toBeInTheDocument();
    });
    expect(
      screen.getByText(/Inorder traversal on BST visits elements in strictly ascending order./i)
    ).toBeInTheDocument();
  });

  it('auto-advances to the next question when the 20s timer expires', async () => {
    // Guest path (no session): engine falls back to local questions, and the
    // 20s timer is the only thing under test. Keep real timers for the async
    // load, then fast-forward the countdown.
    const { authApi } = await import('../src/utils/api');
    vi.spyOn(authApi, 'getMe').mockRejectedValue(new Error('NO_SESSION'));
    try {
      render(
        <AuthProvider>
          <ProgressProvider>
            <QuizEngine
              topicTitle="Arrays & Hashing"
              topicId="arrays-hashing"
              questions={sampleQuestions}
              perQuestionSec={2}
            />
          </ProgressProvider>
        </AuthProvider>
      );

      expect(await screen.findByText(/1. What is the time complexity/i)).toBeInTheDocument();
      // Let the short per-question clock run out (real timers, tight timeout).
      expect(await screen.findByText(/2. Which data structure follows LIFO/i, {}, { timeout: 8000 })).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  }, 15000);

  it('timeout locks the question: advancing then going back disallows answering', async () => {
    const { authApi } = await import('../src/utils/api');
    vi.spyOn(authApi, 'getMe').mockRejectedValue(new Error('NO_SESSION'));
    vi.useFakeTimers();
    try {
      render(
        <AuthProvider>
          <ProgressProvider>
            <QuizEngine
              topicTitle="Arrays & Hashing"
              topicId="arrays-hashing"
              questions={sampleQuestions}
              perQuestionSec={20}
            />
          </ProgressProvider>
        </AuthProvider>
      );

      // Flush the async guest load (refreshUser rejection -> local fallback).
      await act(async () => {
        await vi.advanceTimersByTimeAsync(100);
      });
      expect(screen.getByText(/1. What is the time complexity/i)).toBeInTheDocument();

      // Exhaust the 20s per-question clock (extra tick for boundary).
      await act(async () => {
        await vi.advanceTimersByTimeAsync(21000);
      });

      // Auto-advanced to question 2.
      expect(screen.getByText(/2. Which data structure follows LIFO/i)).toBeInTheDocument();

      // Go back to the timed-out question: it must show locked and refuse answers.
      fireEvent.click(screen.getByText(/← Previous/i));
      expect(screen.getByText(/Timed out — locked/i)).toBeInTheDocument();

      fireEvent.click(screen.getByText('O(log n)'));
      // Selection unchanged: submit counter still shows 0 answered.
      expect(screen.getByText(/Submit Quiz \(0\/2\)/i)).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  }, 15000);
});
