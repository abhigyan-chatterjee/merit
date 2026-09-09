import React, { useState, useEffect, useCallback } from 'react';
import {
  CheckCircle2,
  XCircle,
  RotateCcw,
  Clock,
  Award,
  HelpCircle,
  Sparkles,
  RefreshCw,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import { QuizQuestion } from '../data/quizzes';
import { quizApi, QuizQuestionItem } from '../utils/api';
import { useAuth } from '../store/AuthContext';

interface DisplayQuestion {
  id: string;
  question: string;
  options: string[];
  correctIndex?: number;
  explanation?: string;
  difficulty?: string;
  topic?: string;
}

/** Stable default so `loadQuiz` identity doesn't churn every render. */
const NO_QUESTIONS: QuizQuestion[] = [];

interface QuizEngineProps {
  topicTitle: string;
  topicId: string;
  questions?: QuizQuestion[];
  isMock?: boolean;
  durationLimitSec?: number;
  /** Targeted-exam overrides: explicit topic list / count / difficulty */
  examTopics?: string[];
  examCount?: number;
  examDifficulty?: string;
  /** Quizzes: 20s hard per-question timer. Exams use their own countdown. */
  perQuestionSec?: number | null;
  onComplete?: (scorePercentage: number) => void;
}

/** Default quiz timing: 20s per MCQ with hard auto-advance. Null = untimed. */
export const QUIZ_PER_QUESTION_SEC = 20;

export const QuizEngine: React.FC<QuizEngineProps> = ({
  topicTitle,
  topicId,
  questions = NO_QUESTIONS,
  isMock = false,
  durationLimitSec = 1800,
  examTopics,
  examCount,
  examDifficulty,
  perQuestionSec = QUIZ_PER_QUESTION_SEC,
  onComplete,
}) => {
  const { user, refreshUser } = useAuth();

  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [activeQuestions, setActiveQuestions] = useState<DisplayQuestion[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, number>>({});
  const [submitted, setSubmitted] = useState(false);
  const [secondsElapsed, setSecondsElapsed] = useState(0);
  const [secondsRemaining, setSecondsRemaining] = useState(durationLimitSec);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [questionTimeLeft, setQuestionTimeLeft] = useState<number>(perQuestionSec ?? 0);
  // Echo of the topics the server actually sampled from (debuggability).
  const [servedTopics, setServedTopics] = useState<string[] | null>(null);


  // Server results map: question_id -> result details
  const [serverResults, setServerResults] = useState<
    Record<
      string,
      {
        correctIndex: number;
        explanation: string;
        isCorrect: boolean;
      }
    >
  >({});
  const [serverSummary, setServerSummary] = useState<{
    total: number;
    correct: number;
    scorePct: number;
  } | null>(null);

  // Initialize or fetch quiz. Runs once on mount with a refresh-first
  // auth check: `user` from context may still be null on first paint even
  // when a session cookie exists, so resolve the session here instead of
  // depending on possibly-stale context state.
  const loadQuiz = useCallback(async () => {
    setIsLoading(true);
    setLoadError(null);
    setSelectedAnswers({});
    setSubmitted(false);
    setSecondsElapsed(0);
    setSecondsRemaining(durationLimitSec);
    setQuestionTimeLeft(perQuestionSec ?? 0);
    setCurrentIndex(0);
    setServerResults({});
    setServerSummary(null);
    setServedTopics(null);

    try {
      // Prefer already-resolved context state (covers StrictMode remounts
      // and tests that set the session before mount); only hit the network
      // when context has no user yet.
      let activeUser = user;
      if (!activeUser) {
        try {
          activeUser = await refreshUser();
        } catch {
          activeUser = null;
        }
      }
      if (activeUser) {
        const topics =
          examTopics && examTopics.length > 0
            ? examTopics
            : topicId === 'mixed'
            ? ['arrays-hashing', 'trees', 'graphs', 'dynamic-programming']
            : [topicId];
        const count = examCount ?? (isMock ? 20 : 10);
        const res = await quizApi.generateQuiz(
          topics,
          count,
          examDifficulty,
          isMock,
          durationLimitSec
        );
        if (res.questions && res.questions.length > 0) {
          setAttemptId(res.attempt_id);
          if (res.duration_sec) {
            setSecondsRemaining(res.duration_sec);
          }
          setServedTopics([...new Set(res.questions.map((q) => q.topic))]);
          setActiveQuestions(
            res.questions.map((q: QuizQuestionItem) => ({
              id: q.id,
              question: q.prompt,
              options: q.options,
              difficulty: q.difficulty,
              topic: q.topic,
            }))
          );
          setIsLoading(false);
          return;
        }
      }
    } catch (err: unknown) {
      if (err instanceof Error && err.message === 'NO_SESSION') {
        // fall through to local bank below
      } else {
        console.warn('Server quiz generation fallback to local questions:', err);
      }
    }

    // Fallback: local questions are already scoped per topic by QuizPage
    // (QUIZZES[currentTopic.id]), so render them as-is. The key={topicId}
    // remount plus the loadQuiz deps above guarantee a topic switch reloads.
    setAttemptId(null);
    setServedTopics(null);
    if (questions && questions.length > 0) {
      setActiveQuestions(
        questions.map((q) => ({
          id: q.id,
          question: q.question,
          options: q.options,
          correctIndex: q.correctIndex,
          explanation: q.explanation,
        }))
      );
    } else {
      setLoadError('No questions available for this topic yet.');
    }
    setIsLoading(false);
  }, [user, topicId, isMock, durationLimitSec, examTopics, examCount, examDifficulty, perQuestionSec, questions, refreshUser]);

  useEffect(() => {
    loadQuiz();
  }, [loadQuiz]);

  // Timer: count-up always; mock/exam countdown with auto-submit;
  // quizzes (non-mock, perQuestionSec set) get a hard per-question timer
  // that auto-advances. Unanswered questions count as wrong at submit.
  // Note: submit callback is invoked via ref-stable gradeLocally path to
  // avoid referencing handleSubmitQuiz before its declaration.
  useEffect(() => {
    if (submitted || isLoading) return;
    const timer = setInterval(() => {
      setSecondsElapsed((s) => s + 1);
      if (isMock) {
        setSecondsRemaining((rem) => {
          if (rem <= 1) {
            clearInterval(timer);
            setSecondsRemaining(0);
            return 0;
          }
          return rem - 1;
        });
      } else if (perQuestionSec && perQuestionSec > 0) {
        setQuestionTimeLeft((left) => {
          if (left <= 1) {
            // Time up on this MCQ: advance (or finish on the last one).
            setCurrentIndex((i) => {
              if (i >= activeQuestions.length - 1) {
                clearInterval(timer);
              }
              return Math.min(activeQuestions.length - 1, i + 1);
            });
            return perQuestionSec;
          }
          return left - 1;
        });
      }
    }, 1000);
    return () => clearInterval(timer);
  }, [submitted, isLoading, isMock, perQuestionSec, activeQuestions.length]);

  // Reset the per-question clock whenever the question changes.
  useEffect(() => {
    if (!isMock && perQuestionSec && perQuestionSec > 0) {
      setQuestionTimeLeft(perQuestionSec);
    }
  }, [currentIndex, isMock, perQuestionSec]);


  const currentQ = activeQuestions[currentIndex];

  const handleSelectOption = (idx: number) => {
    if (submitted || !currentQ) return;
    setSelectedAnswers((prev) => ({ ...prev, [currentQ.id]: idx }));
  };

  const gradeLocally = () => {
    let correct = 0;
    const resultsMap: Record<string, { correctIndex: number; explanation: string; isCorrect: boolean }> = {};
    for (const q of activeQuestions) {
      const cIdx = q.correctIndex ?? 0;
      const isCorr = selectedAnswers[q.id] === cIdx;
      if (isCorr) correct++;
      resultsMap[q.id] = {
        correctIndex: cIdx,
        explanation: q.explanation || 'Refer to fundamental principles.',
        isCorrect: isCorr,
      };
    }
    const pct = Math.round((correct / activeQuestions.length) * 100);
    setServerResults(resultsMap);
    setServerSummary({
      total: activeQuestions.length,
      correct,
      scorePct: pct,
    });
    setSubmitted(true);
    onComplete?.(pct);
  };

  const handleSubmitQuiz = async () => {
    if (submitted || activeQuestions.length === 0) return;

    if (attemptId) {
      // Server-verified grading
      setIsSubmitting(true);
      try {
        const res = await quizApi.submitQuiz(attemptId, secondsElapsed, selectedAnswers);
        const resultsMap: Record<string, { correctIndex: number; explanation: string; isCorrect: boolean }> = {};
        for (const item of res.results) {
          resultsMap[item.question_id] = {
            correctIndex: item.correct_index,
            explanation: item.explanation,
            isCorrect: item.is_correct,
          };
        }
        setServerResults(resultsMap);
        setServerSummary({
          total: res.total,
          correct: res.correct,
          scorePct: res.score_pct,
        });
        setSubmitted(true);
        onComplete?.(res.score_pct);
      } catch (err: unknown) {
        console.error('Failed to submit quiz to server:', err);
        // Fallback local grading if server submission fails
        gradeLocally();
      } finally {
        setIsSubmitting(false);
      }
    } else {
      // Local grading
      gradeLocally();
    }
  };

  const handleRetryWrongOnly = async () => {
    if (attemptId) {
      setIsLoading(true);
      try {
        const res = await quizApi.retryWrong(attemptId);
        if (res.questions && res.questions.length > 0) {
          setAttemptId(res.attempt_id);
          setActiveQuestions(
            res.questions.map((q: QuizQuestionItem) => ({
              id: q.id,
              question: q.prompt,
              options: q.options,
              difficulty: q.difficulty,
              topic: q.topic,
            }))
          );
          setCurrentIndex(0);
          setSelectedAnswers({});
          setSubmitted(false);
          setSecondsElapsed(0);
          setServerResults({});
          setServerSummary(null);
          setIsLoading(false);
          return;
        }
      } catch (err) {
        console.warn('Failed to retry wrong questions via server:', err);
      }
    }

    // Local retry wrong
    const wrongList = activeQuestions.filter((q) => {
      const res = serverResults[q.id];
      if (res) return !res.isCorrect;
      return selectedAnswers[q.id] !== q.correctIndex;
    });

    if (wrongList.length === 0) return;
    setActiveQuestions(wrongList);
    setCurrentIndex(0);
    setSelectedAnswers({});
    setSubmitted(false);
    setSecondsElapsed(0);
    setServerResults({});
    setServerSummary(null);
    setIsLoading(false);
  };

  const formatTime = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  // Auto-submit the mock exam when the countdown hits zero. Placed after
  // handleSubmitQuiz is defined so the effect never references a binding
  // that is still in its temporal dead zone.
  useEffect(() => {
    if (isMock && !submitted && !isLoading && secondsRemaining <= 0 && activeQuestions.length > 0) {
      void handleSubmitQuiz();
    }
  }, [isMock, submitted, isLoading, secondsRemaining, activeQuestions.length]); // eslint-disable-line react-hooks/exhaustive-deps

  const correctCount = serverSummary
    ? serverSummary.correct
    : activeQuestions.filter((q) => {
        const res = serverResults[q.id];
        return res ? res.isCorrect : selectedAnswers[q.id] === q.correctIndex;
      }).length;

  const scorePct = serverSummary
    ? serverSummary.scorePct
    : Math.round((correctCount / (activeQuestions.length || 1)) * 100);

  if (isLoading) {
    return (
      <div className="p-12 rounded-xl border border-line bg-surface flex flex-col items-center justify-center space-y-4 text-center">
        <RefreshCw className="w-8 h-8 text-mint animate-spin" />
        <div>
          <h3 className="text-sm font-semibold text-ink">Sampling Verified Questions...</h3>
          <p className="text-xs text-muted mt-1">
            Balancing difficulty curve (40% Easy / 40% Med / 20% Hard) & preventing repeats.
          </p>
        </div>
      </div>
    );
  }

  if (loadError || activeQuestions.length === 0) {
    return (
      <div className="p-8 rounded-xl border border-line bg-surface text-center space-y-4">
        <AlertCircle className="w-8 h-8 text-amber mx-auto" />
        <div>
          <h3 className="text-sm font-semibold text-ink">No Questions Available</h3>
          <p className="text-xs text-muted mt-1">
            {loadError || 'Unable to load questions for this topic.'}
          </p>
        </div>
        <button
          onClick={loadQuiz}
          className="px-4 py-2 rounded-lg bg-mint text-canvas text-xs font-semibold hover:brightness-110 transition cursor-pointer"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Sticky Mock Exam Banner */}
      {isMock && !submitted && (
        <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl bg-surface border border-amber/70 shadow-xl">
          <div className="flex items-center gap-2.5">
            <Clock className="w-5 h-5 text-amber" />
            <div>
              <div className="text-xs font-bold text-ink uppercase tracking-wider">
                Placement Timed Mock Exam
              </div>
              <div className="text-[10px] font-mono text-muted">
                {activeQuestions.length} questions across topics · Auto-submits on timeout
              </div>
            </div>
          </div>
          <div className="px-3.5 py-1.5 rounded-lg bg-amber/15 border border-amber/40 font-mono text-sm font-bold text-amber flex items-center gap-2">
            <span>Remaining:</span>
            <span>{formatTime(secondsRemaining)}</span>
          </div>
        </div>
      )}

      {/* Quiz Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl border border-line bg-surface">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-ink">
              {isMock ? 'Placement Mock Examination' : `${topicTitle} Mastery Quiz`}
            </h2>

            {attemptId && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-medium bg-mint/15 text-mint border border-mint/30">
                <Sparkles className="w-2.5 h-2.5" />
                Verified Bank
              </span>
            )}
          </div>
          <p className="text-xs text-muted">
            Question {currentIndex + 1} of {activeQuestions.length}
            {currentQ?.difficulty && (
              <span className="ml-2 font-mono text-[10px] uppercase text-muted/80">
                • {currentQ.difficulty}
              </span>
            )}
            {servedTopics && servedTopics.length > 0 && (
              <span className="ml-2 font-mono text-[10px] text-muted/80">
                • bank: {servedTopics.join(', ')}
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {!isMock && !submitted && perQuestionSec != null && perQuestionSec > 0 && (
            <div
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg bg-canvas border font-mono text-xs font-bold ${
                questionTimeLeft <= 5 ? 'border-rose/60 text-rose' : 'border-amber/40 text-amber'
              }`}
              title="Time left for this question — auto-advances at zero"
            >
              <Clock className="w-3.5 h-3.5" />
              <span>0:{String(questionTimeLeft).padStart(2, '0')}</span>
            </div>
          )}
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-canvas border border-line font-mono text-xs text-ink">
            <Clock className="w-3.5 h-3.5 text-mint" />
            <span>{formatTime(secondsElapsed)}</span>
          </div>

          {submitted && (
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-mint/15 border border-mint font-mono text-xs text-mint font-bold">
              <Award className="w-4 h-4" />
              Score: {scorePct}% ({correctCount}/{activeQuestions.length})
            </div>
          )}
        </div>
      </div>

      {/* Question Card */}
      {currentQ && (
        <div className="p-6 rounded-xl border border-line bg-surface space-y-5">
          <div className="flex items-start justify-between gap-4">
            <h3 className="text-base font-semibold text-ink leading-relaxed">
              {currentIndex + 1}. {currentQ.question}
            </h3>
          </div>

          {/* MCQ Option Buttons */}
          <div className="space-y-2.5">
            {currentQ.options.map((opt, idx) => {
              const isSelected = selectedAnswers[currentQ.id] === idx;
              const resultInfo = serverResults[currentQ.id];
              const isCorrect = resultInfo
                ? resultInfo.correctIndex === idx
                : currentQ.correctIndex === idx;

              let btnClass = 'border-line bg-canvas text-ink hover:border-muted';
              if (submitted) {
                if (isCorrect) {
                  btnClass = 'border-mint bg-mint/15 text-mint font-semibold';
                } else if (isSelected && !isCorrect) {
                  btnClass = 'border-rose bg-rose/15 text-rose';
                }
              } else if (isSelected) {
                btnClass = 'border-mint bg-mint/10 text-mint font-semibold';
              }

              return (
                <button
                  key={idx}
                  onClick={() => handleSelectOption(idx)}
                  disabled={submitted || isSubmitting}
                  className={`w-full text-left p-3.5 rounded-lg border text-xs font-mono transition flex items-center justify-between cursor-pointer ${btnClass}`}
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded flex items-center justify-center border border-current text-[11px] shrink-0">
                      {String.fromCharCode(65 + idx)}
                    </span>
                    <span>{opt}</span>
                  </div>

                  {submitted && isCorrect && <CheckCircle2 className="w-4 h-4 text-mint shrink-0" />}
                  {submitted && isSelected && !isCorrect && (
                    <XCircle className="w-4 h-4 text-rose shrink-0" />
                  )}
                </button>
              );
            })}
          </div>

          {/* Explanation Box after Submit */}
          {submitted && (
            <div className="p-4 rounded-lg border border-violet/40 bg-violet/10 text-xs space-y-1">
              <div className="font-mono font-semibold text-violet flex items-center gap-1.5">
                <HelpCircle className="w-4 h-4" />
                Algorithmic Explanation:
              </div>
              <p className="text-ink leading-relaxed">
                {serverResults[currentQ.id]?.explanation ||
                  currentQ.explanation ||
                  'Verified algorithmic explanation.'}
              </p>
            </div>
          )}

          {/* Question Navigation Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-line">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
                disabled={currentIndex === 0 || isSubmitting}
                className="px-3 py-1.5 rounded-lg border border-line bg-canvas text-xs font-mono text-ink disabled:opacity-40 cursor-pointer hover:border-muted transition"
              >
                ← Previous
              </button>
              <button
                onClick={() => setCurrentIndex((i) => Math.min(activeQuestions.length - 1, i + 1))}
                disabled={currentIndex === activeQuestions.length - 1 || isSubmitting}
                className="px-3 py-1.5 rounded-lg border border-line bg-canvas text-xs font-mono text-ink disabled:opacity-40 cursor-pointer hover:border-muted transition"
              >
                Next →
              </button>
            </div>

            <div className="flex items-center gap-2">
              {!submitted ? (
                <button
                  onClick={handleSubmitQuiz}
                  disabled={isSubmitting}
                  className="px-4 py-1.5 rounded-lg bg-mint text-canvas font-semibold text-xs hover:brightness-110 transition cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
                >
                  {isSubmitting ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      Grading...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-3.5 h-3.5" />
                      Submit Quiz ({Object.keys(selectedAnswers).length}/{activeQuestions.length})
                    </>
                  )}
                </button>
              ) : (
                <>
                  {correctCount < activeQuestions.length && (
                    <button
                      onClick={handleRetryWrongOnly}
                      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-amber text-canvas font-semibold text-xs hover:brightness-110 transition cursor-pointer"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                      Retry Wrong Only ({activeQuestions.length - correctCount})
                    </button>
                  )}

                  <button
                    onClick={loadQuiz}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg border border-line bg-canvas text-xs font-mono text-ink hover:border-mint transition cursor-pointer"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    New Assessment
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
