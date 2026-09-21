import React, { useCallback, useEffect, useRef, useState } from 'react';
import { quizApi, QuizQuestionItem } from '../utils/api';

export interface ExamMcqSectionProps {
  examId: string;
  examTitle: string;
  topics: string[];
  questionCount: number;
  difficulty: string;
  topicPlan?: [string, number][];
  durationSec: number;
  currentIndex: number;
  onCurrentIndexChange: (index: number) => void;
  onAnswersChange: (answers: Record<string, number>) => void;
  onQuestionIdsChange: (ids: string[]) => void;
  onComplete: (scorePct: number) => void;
  isAutoSubmitRequested?: boolean;
}

type ExamQuestion = QuizQuestionItem & { correctIndex?: number };

export const ExamMcqSection: React.FC<ExamMcqSectionProps> = ({
  examId,
  examTitle,
  topics,
  questionCount,
  difficulty,
  topicPlan,
  durationSec,
  currentIndex,
  onCurrentIndexChange,
  onAnswersChange,
  onQuestionIdsChange,
  onComplete,
  isAutoSubmitRequested = false,
}) => {
  const [questions, setQuestions] = useState<ExamQuestion[]>([]);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, number>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<{ correct: number; total: number; scorePct: number; correctById: Record<string, boolean> } | null>(null);
  const [retryKey, setRetryKey] = useState(0);
  const submitStartedRef = useRef(false);
  const callbacksRef = useRef({ onAnswersChange, onComplete, onCurrentIndexChange, onQuestionIdsChange });
  callbacksRef.current = { onAnswersChange, onComplete, onCurrentIndexChange, onQuestionIdsChange };

  const loadQuestions = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    setSubmitError(null);
    setQuestions([]);
    setAnswers({});
    setAttemptId(null);
    setSubmitted(false);
    setResult(null);
    submitStartedRef.current = false;
    try {
      const response = await quizApi.generateQuiz(
        topics,
        questionCount,
        difficulty,
        true,
        durationSec,
        topicPlan,
      );
      const loaded = response.questions as ExamQuestion[];
      setQuestions(loaded);
      setAttemptId(response.attempt_id || null);
      callbacksRef.current.onQuestionIdsChange(loaded.map((question) => question.id));
      callbacksRef.current.onAnswersChange({});
      callbacksRef.current.onCurrentIndexChange(0);
    } catch (error) {
      console.error('Failed to load exam questions:', error);
      setLoadError('Could not load the exam questions. Please try again.');
      onQuestionIdsChange([]);
    } finally {
      setIsLoading(false);
    }
  }, [durationSec, difficulty, examId, questionCount, retryKey, topicPlan, topics]);

  useEffect(() => {
    void loadQuestions();
  }, [loadQuestions]);

  const submitExam = useCallback(async () => {
    if (submitStartedRef.current || submitted || questions.length === 0) return;
    submitStartedRef.current = true;
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      let correct = 0;
      let correctById: Record<string, boolean> = {};
      let scorePct: number;
      let total = questions.length;

      if (attemptId) {
        const response = await quizApi.submitQuiz(attemptId, durationSec, answers);
        correct = response.correct;
        total = response.total;
        scorePct = response.score_pct;
        correctById = Object.fromEntries(
          response.results.map((item) => [item.question_id, item.is_correct]),
        );
      } else {
        correctById = Object.fromEntries(
          questions.map((question) => {
            const isCorrect = question.correctIndex !== undefined && answers[question.id] === question.correctIndex;
            return [question.id, isCorrect];
          }),
        );
        correct = Object.values(correctById).filter(Boolean).length;
        scorePct = total > 0 ? Math.round((correct / total) * 100) : 0;
      }

      setResult({ correct, total, scorePct, correctById });
      setSubmitted(true);
      callbacksRef.current.onComplete(scorePct);
    } catch (error) {
      console.error('Failed to submit exam:', error);
      submitStartedRef.current = false;
      setSubmitError('Could not submit the exam. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }, [answers, attemptId, durationSec, questions, submitted]);

  useEffect(() => {
    if (isAutoSubmitRequested) void submitExam();
  }, [isAutoSubmitRequested, submitExam]);

  const currentQuestion = questions[currentIndex];
  const answered = Object.keys(answers).length;

  if (isLoading) {
    return <div role="status" className="rounded-xl border border-line bg-surface p-6 text-sm text-muted">Loading exam questions…</div>;
  }

  if (loadError) {
    return (
      <div className="rounded-xl border border-rose/40 bg-rose/10 p-6 space-y-3 text-center">
        <p role="alert" className="text-sm text-rose">{loadError}</p>
        <button type="button" onClick={() => setRetryKey((key) => key + 1)} className="rounded-lg bg-violet px-4 py-2 text-xs font-semibold text-canvas">
          Try Again
        </button>
      </div>
    );
  }

  if (submitted && result) {
    return (
      <section aria-label={`${examTitle} result`} className="rounded-xl border border-mint/40 bg-surface p-6 space-y-5">
        <div>
          <h2 className="text-lg font-bold text-ink">Exam Result</h2>
          <p className="mt-1 text-3xl font-bold text-mint">{result.scorePct}%</p>
        </div>
        <p className="text-sm text-muted">Correct: {result.correct}/{result.total}</p>
        <div className="space-y-1.5">
          <h3 className="text-xs font-bold uppercase tracking-wider text-muted">Review breakdown</h3>
          {questions.map((question, index) => (
            <div key={question.id} className="flex justify-between gap-3 text-xs">
              <span className="truncate text-ink">Question {index + 1}</span>
              <span className={result.correctById[question.id] ? 'text-mint' : 'text-rose'}>
                {result.correctById[question.id] ? 'Correct' : 'Incorrect'}
              </span>
            </div>
          ))}
        </div>
      </section>
    );
  }

  if (!currentQuestion) {
    return <div role="alert" className="rounded-xl border border-rose/40 bg-rose/10 p-6 text-sm text-rose">No questions are available for this exam.</div>;
  }

  const selectAnswer = (index: number) => {
    const nextAnswers = { ...answers, [currentQuestion.id]: index };
    setAnswers(nextAnswers);
    callbacksRef.current.onAnswersChange(nextAnswers);
  };

  return (
    <section aria-label={`${examTitle} multiple choice questions`} className="rounded-xl border border-line bg-surface p-5 space-y-5">
      <div className="flex items-center justify-between gap-3 text-xs font-mono text-muted">
        <span>Question {currentIndex + 1} of {questions.length}</span>
        <span>{answered}/{questions.length} answered</span>
      </div>
      <div className="space-y-4">
        <h3 className="text-base font-semibold leading-relaxed text-ink">{currentQuestion.prompt}</h3>
        <div className="space-y-2">
          {currentQuestion.options.map((option, index) => (
            <button
              type="button"
              key={`${currentQuestion.id}-${index}`}
              aria-pressed={answers[currentQuestion.id] === index}
              onClick={() => selectAnswer(index)}
              className={`w-full rounded-lg border px-4 py-3 text-left text-sm transition ${
                answers[currentQuestion.id] === index ? 'border-mint bg-mint/10 text-ink' : 'border-line text-ink hover:border-violet'
              }`}
            >
              <span className="mr-2 font-mono text-muted">{String.fromCharCode(65 + index)}.</span>{option}
            </button>
          ))}
        </div>
      </div>
      {submitError && <p role="alert" className="text-xs text-rose">{submitError}</p>}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <button type="button" disabled={currentIndex === 0} onClick={() => callbacksRef.current.onCurrentIndexChange(currentIndex - 1)} className="rounded-lg border border-line px-3 py-2 text-xs text-ink disabled:opacity-40">← Previous</button>
        <button type="button" onClick={() => void submitExam()} disabled={isSubmitting} className="rounded-lg bg-violet px-4 py-2 text-xs font-semibold text-canvas disabled:opacity-50">
          {isSubmitting ? 'Submitting…' : `Submit Exam (${answered}/${questions.length})`}
        </button>
        <button type="button" disabled={currentIndex >= questions.length - 1} onClick={() => callbacksRef.current.onCurrentIndexChange(currentIndex + 1)} className="rounded-lg border border-line px-3 py-2 text-xs text-ink disabled:opacity-40">Next →</button>
      </div>
    </section>
  );
};
