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
  const [isRetryDrill, setIsRetryDrill] = useState(false);
  const [drillQuestions, setDrillQuestions] = useState<ExamQuestion[]>([]);
  const [drillAttemptId, setDrillAttemptId] = useState<string | null>(null);
  const [drillAnswers, setDrillAnswers] = useState<Record<string, number>>({});
  const [drillIndex, setDrillIndex] = useState(0);
  const [drillResult, setDrillResult] = useState<{ correct: number; total: number; scorePct: number; correctById: Record<string, boolean> } | null>(null);
  const [isDrillSubmitting, setIsDrillSubmitting] = useState(false);
  const [drillError, setDrillError] = useState<string | null>(null);
  const [isDrillLoading, setIsDrillLoading] = useState(false);
  const [retryKey, setRetryKey] = useState(0);
  const loadRunRef = useRef(0);
  const inflightRef = useRef<{ key: string; promise: ReturnType<typeof quizApi.generateQuiz> } | null>(null);
  const submitStartedRef = useRef(false);
  const callbacksRef = useRef({ onAnswersChange, onComplete, onCurrentIndexChange, onQuestionIdsChange });
  useEffect(() => {
    callbacksRef.current = { onAnswersChange, onComplete, onCurrentIndexChange, onQuestionIdsChange };
  });

  // `topics`/`topicPlan` can arrive as fresh array literals from the caller.
  // Listing them directly in the deps below would re-create the loader on every
  // render, re-fetching and resetting the exam mid-session. Depend on their
  // serialized contents instead, so the loader only changes when the exam does.
  const topicsKey = JSON.stringify(topics);
  const topicPlanKey = JSON.stringify(topicPlan ?? null);

  const loadQuestions = useCallback(async () => {
    const runToken = ++loadRunRef.current;
    const isStale = () => runToken !== loadRunRef.current;
    const key = JSON.stringify([
      examId,
      topicsKey,
      topicPlanKey,
      questionCount,
      difficulty,
      durationSec,
      retryKey,
    ]);

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
      let response;
      if (inflightRef.current && inflightRef.current.key === key) {
        response = await inflightRef.current.promise;
      } else {
        const promise = quizApi.generateQuiz(
          topics,
          questionCount,
          difficulty,
          true,
          durationSec,
          topicPlan,
        );
        inflightRef.current = { key, promise };
        try {
          response = await promise;
        } finally {
          if (inflightRef.current && inflightRef.current.key === key) {
            inflightRef.current = null;
          }
        }
      }
      if (isStale()) return;
      const loaded = (response?.questions || []) as ExamQuestion[];
      setQuestions(loaded);
      setAttemptId(response?.attempt_id || null);
      callbacksRef.current.onQuestionIdsChange(loaded.map((question) => question.id));
      callbacksRef.current.onAnswersChange({});
      callbacksRef.current.onCurrentIndexChange(0);
    } catch (error) {
      if (isStale()) return;
      console.error('Failed to load exam questions:', error);
      setLoadError('Could not load the exam questions. Please try again.');
      callbacksRef.current.onQuestionIdsChange([]);
    } finally {
      if (!isStale()) setIsLoading(false);
    }
    // Reads `topics`/`topicPlan` through the closure, guarded by their
    // serialized keys above rather than by array identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [durationSec, difficulty, examId, questionCount, retryKey, topicsKey, topicPlanKey]);

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

  const startRetryDrill = useCallback(async () => {
    if (!result) return;
    setDrillError(null);
    setDrillResult(null);
    setDrillAnswers({});
    setDrillIndex(0);
    if (attemptId) {
      setIsDrillLoading(true);
      try {
        const retry = await quizApi.retryWrong(attemptId);
        if (retry.questions && retry.questions.length > 0) {
          setDrillQuestions(retry.questions as ExamQuestion[]);
          setDrillAttemptId(retry.attempt_id);
          setIsRetryDrill(true);
          return;
        }
      } catch {
        // Fall through to local missed questions.
      } finally {
        setIsDrillLoading(false);
      }
    }
    const missed = questions.filter((q) => !result.correctById[q.id]);
    setDrillQuestions(missed);
    setDrillAttemptId(null);
    setIsRetryDrill(true);
  }, [attemptId, questions, result]);

  const submitDrill = useCallback(async () => {
    if (drillQuestions.length === 0 || isDrillSubmitting) return;
    setIsDrillSubmitting(true);
    setDrillError(null);
    try {
      if (drillAttemptId) {
        const response = await quizApi.submitQuiz(drillAttemptId, durationSec, drillAnswers);
        setDrillResult({
          correct: response.correct,
          total: response.total,
          scorePct: response.score_pct,
          correctById: Object.fromEntries(response.results.map((item) => [item.question_id, item.is_correct])),
        });
      } else {
        const correctById: Record<string, boolean> = Object.fromEntries(
          drillQuestions.map((q) => {
            const isCorrect = q.correctIndex !== undefined && drillAnswers[q.id] === q.correctIndex;
            return [q.id, isCorrect];
          })
        );
        const correct = Object.values(correctById).filter(Boolean).length;
        const total = drillQuestions.length;
        setDrillResult({
          correct,
          total,
          scorePct: total > 0 ? Math.round((correct / total) * 100) : 0,
          correctById,
        });
      }
    } catch {
      setDrillError('Could not grade the practice drill. Please try again.');
    } finally {
      setIsDrillSubmitting(false);
    }
  }, [drillAnswers, drillAttemptId, drillQuestions, durationSec, isDrillSubmitting]);

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

  const currentQuestion = questions[currentIndex];
  const answered = Object.keys(answers).length;

  if (submitted && result) {
    const grouped = new Map<string, { correct: number; total: number }>();
    for (const q of questions) {
      const topic = q.topic || 'general';
      const entry = grouped.get(topic) ?? { correct: 0, total: 0 };
      entry.total += 1;
      if (result.correctById[q.id]) entry.correct += 1;
      grouped.set(topic, entry);
    }
    const topicRows = Array.from(grouped.entries())
      .map(([topic, v]) => ({
        topic,
        correct: v.correct,
        total: v.total,
        pct: v.total > 0 ? Math.round((v.correct / v.total) * 100) : 0,
      }))
      .sort((a, b) => a.pct - b.pct);
    const wrongCount = result.total - result.correct;
    const topicBarTone = (pct: number) => (pct >= 80 ? 'bg-mint' : pct >= 60 ? 'bg-amber' : 'bg-rose');
    const topicTextTone = (pct: number) => (pct >= 80 ? 'text-mint' : pct >= 60 ? 'text-amber' : 'text-rose');

    if (isRetryDrill) {
      const drillQ = drillQuestions[drillIndex];
      const drillAnswered = Object.keys(drillAnswers).length;
      return (
        <section aria-label={`${examTitle} practice drill`} className="rounded-xl border border-amber/40 bg-surface p-6 space-y-5">
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-amber/10 border border-amber/30 text-xs font-semibold text-amber">
            <span>Practice Drill — Missed Questions</span>
          </div>
          {isDrillLoading && <p role="status" className="text-sm text-muted">Loading missed questions…</p>}
          {!isDrillLoading && !drillResult && drillQ && (
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-3 text-xs font-mono text-muted">
                <span>Drill Question {drillIndex + 1} of {drillQuestions.length}</span>
                <span>{drillAnswered}/{drillQuestions.length} answered</span>
              </div>
              <h3 className="text-base font-semibold leading-relaxed text-ink">{drillQ.prompt}</h3>
              <div className="space-y-2">
                {drillQ.options.map((option, index) => (
                  <button
                    type="button"
                    key={`${drillQ.id}-${index}`}
                    aria-pressed={drillAnswers[drillQ.id] === index}
                    onClick={() => setDrillAnswers((prev) => ({ ...prev, [drillQ.id]: index }))}
                    className={`w-full rounded-lg border px-4 py-3 text-left text-sm transition ${
                      drillAnswers[drillQ.id] === index ? 'border-mint bg-mint/10 text-ink' : 'border-line text-ink hover:border-violet'
                    }`}
                  >
                    <span className="mr-2 font-mono text-muted">{String.fromCharCode(65 + index)}.</span>{option}
                  </button>
                ))}
              </div>
              {drillError && <p role="alert" className="text-xs text-rose">{drillError}</p>}
              <div className="flex flex-wrap items-center justify-between gap-3">
                <button
                  type="button"
                  disabled={drillIndex === 0}
                  onClick={() => setDrillIndex((i) => Math.max(0, i - 1))}
                  className="rounded-lg border border-line px-3 py-2 text-xs text-ink disabled:opacity-40"
                >
                  ← Previous
                </button>
                <button
                  type="button"
                  onClick={() => void submitDrill()}
                  disabled={isDrillSubmitting}
                  className="rounded-lg bg-amber px-4 py-2 text-xs font-semibold text-canvas disabled:opacity-50"
                >
                  {isDrillSubmitting ? 'Grading…' : `Submit Drill (${drillAnswered}/${drillQuestions.length})`}
                </button>
                <button
                  type="button"
                  disabled={drillIndex >= drillQuestions.length - 1}
                  onClick={() => setDrillIndex((i) => Math.min(drillQuestions.length - 1, i + 1))}
                  className="rounded-lg border border-line px-3 py-2 text-xs text-ink disabled:opacity-40"
                >
                  Next →
                </button>
              </div>
            </div>
          )}
          {!isDrillLoading && drillResult && (
            <div className="space-y-2">
              <p className="text-sm text-muted">Drill score: {drillResult.correct}/{drillResult.total} ({drillResult.scorePct}%)</p>
              <div className="space-y-1.5">
                {drillQuestions.map((q, index) => (
                  <div key={q.id} className="flex justify-between gap-3 text-xs">
                    <span className="truncate text-ink">Question {index + 1}</span>
                    <span className={drillResult.correctById[q.id] ? 'text-mint' : 'text-rose'}>
                      {drillResult.correctById[q.id] ? 'Correct' : 'Incorrect'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {drillError && drillResult === null && !drillQ && <p role="alert" className="text-xs text-rose">{drillError}</p>}
          <button
            type="button"
            onClick={() => setIsRetryDrill(false)}
            className="rounded-lg border border-line px-4 py-2 text-xs text-ink"
          >
            Back to Exam Result
          </button>
        </section>
      );
    }

    return (
      <section role="status" aria-label={`${examTitle} result`} className="rounded-xl border border-mint/40 bg-surface p-6 space-y-5">
        <div>
          <h2 className="text-lg font-bold text-ink">Exam Result</h2>
          <p className="mt-1 text-3xl font-bold text-mint">{result.scorePct}%</p>
        </div>
        <p className="text-sm text-muted">Correct: {result.correct}/{result.total}</p>
        <div className="space-y-2.5">
          <h3 className="text-xs font-bold uppercase tracking-wider text-muted">Weak-Topic Breakdown</h3>
          {topicRows.map((row) => (
            <div key={row.topic} className="space-y-1">
              <div className="flex items-center justify-between gap-3 text-xs">
                <span className="truncate text-ink">{row.topic}</span>
                <span className="flex items-center gap-2 shrink-0">
                  <span className={`font-mono tnum ${topicTextTone(row.pct)}`}>
                    {row.correct}/{row.total} · {row.pct}%
                  </span>
                  {row.pct < 70 && (
                    <span className="px-1.5 py-0.5 rounded border text-[10px] font-mono font-semibold bg-rose/15 text-rose border-rose/30">
                      Weak
                    </span>
                  )}
                </span>
              </div>
              <span className="block h-1.5 rounded-full bg-line overflow-hidden">
                <span className={`block h-full rounded-full ${topicBarTone(row.pct)}`} style={{ width: `${row.pct}%` }} />
              </span>
            </div>
          ))}
        </div>
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
        {wrongCount > 0 && (
          <button
            type="button"
            onClick={() => void startRetryDrill()}
            disabled={isDrillLoading}
            className="rounded-lg bg-amber px-4 py-2 text-xs font-semibold text-canvas disabled:opacity-50"
          >
            {isDrillLoading ? 'Loading drill…' : `Retry Wrong Only (${wrongCount})`}
          </button>
        )}
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
