import React, { useState, useEffect } from 'react';
import { CheckCircle2, XCircle, RotateCcw, Clock, Award, HelpCircle } from 'lucide-react';
import { QuizQuestion } from '../data/quizzes';

interface QuizEngineProps {
  topicTitle: string;
  questions: QuizQuestion[];
  onComplete: (scorePercentage: number) => void;
}

export const QuizEngine: React.FC<QuizEngineProps> = ({
  topicTitle,
  questions,
  onComplete
}) => {
  const [activeQuestions, setActiveQuestions] = useState<QuizQuestion[]>(questions);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, number>>({});
  const [submitted, setSubmitted] = useState(false);
  const [secondsElapsed, setSecondsElapsed] = useState(0);

  useEffect(() => {
    setActiveQuestions(questions);
    setCurrentIndex(0);
    setSelectedAnswers({});
    setSubmitted(false);
    setSecondsElapsed(0);
  }, [questions]);

  useEffect(() => {
    if (submitted) return;
    const timer = setInterval(() => {
      setSecondsElapsed((s) => s + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, [submitted]);

  const currentQ = activeQuestions[currentIndex];

  const handleSelectOption = (idx: number) => {
    if (submitted) return;
    setSelectedAnswers((prev) => ({ ...prev, [currentQ.id]: idx }));
  };

  const handleSubmitQuiz = () => {
    setSubmitted(true);
    let correct = 0;
    for (const q of activeQuestions) {
      if (selectedAnswers[q.id] === q.correctIndex) correct++;
    }
    const pct = Math.round((correct / activeQuestions.length) * 100);
    onComplete(pct);
  };

  const handleRetryWrongOnly = () => {
    const wrongList = activeQuestions.filter(
      (q) => selectedAnswers[q.id] !== q.correctIndex
    );
    if (wrongList.length === 0) return;
    setActiveQuestions(wrongList);
    setCurrentIndex(0);
    setSelectedAnswers({});
    setSubmitted(false);
    setSecondsElapsed(0);
  };

  const handleResetAll = () => {
    setActiveQuestions(questions);
    setCurrentIndex(0);
    setSelectedAnswers({});
    setSubmitted(false);
    setSecondsElapsed(0);
  };

  const formatTime = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const correctCount = activeQuestions.filter(
    (q) => selectedAnswers[q.id] === q.correctIndex
  ).length;
  const scorePct = Math.round((correctCount / activeQuestions.length) * 100);

  return (
    <div className="space-y-6">
      {/* Quiz Top Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 rounded-xl border border-line bg-surface">
        <div>
          <h2 className="text-base font-bold text-ink">{topicTitle} Mastery Quiz</h2>
          <p className="text-xs text-muted">
            Question {currentIndex + 1} of {activeQuestions.length}
          </p>
        </div>

        <div className="flex items-center gap-4">
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
              const isCorrect = currentQ.correctIndex === idx;

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
                  disabled={submitted}
                  className={`w-full text-left p-3.5 rounded-lg border text-xs font-mono transition flex items-center justify-between cursor-pointer ${btnClass}`}
                >
                  <div className="flex items-center gap-3">
                    <span className="w-6 h-6 rounded flex items-center justify-center border border-current text-[11px]">
                      {String.fromCharCode(65 + idx)}
                    </span>
                    <span>{opt}</span>
                  </div>

                  {submitted && isCorrect && <CheckCircle2 className="w-4 h-4 text-mint" />}
                  {submitted && isSelected && !isCorrect && <XCircle className="w-4 h-4 text-rose" />}
                </button>
              );
            })}
          </div>

          {/* Instant Explanation Box after Submit */}
          {submitted && (
            <div className="p-4 rounded-lg border border-violet/40 bg-violet/10 text-xs space-y-1">
              <div className="font-mono font-semibold text-violet flex items-center gap-1.5">
                <HelpCircle className="w-4 h-4" />
                Algorithmic Explanation:
              </div>
              <p className="text-ink leading-relaxed">{currentQ.explanation}</p>
            </div>
          )}

          {/* Question Navigation Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-line">
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentIndex((i) => Math.max(0, i - 1))}
                disabled={currentIndex === 0}
                className="px-3 py-1.5 rounded-lg border border-line bg-canvas text-xs font-mono text-ink disabled:opacity-40 cursor-pointer"
              >
                ← Previous
              </button>
              <button
                onClick={() => setCurrentIndex((i) => Math.min(activeQuestions.length - 1, i + 1))}
                disabled={currentIndex === activeQuestions.length - 1}
                className="px-3 py-1.5 rounded-lg border border-line bg-canvas text-xs font-mono text-ink disabled:opacity-40 cursor-pointer"
              >
                Next →
              </button>
            </div>

            <div className="flex items-center gap-2">
              {!submitted ? (
                <button
                  onClick={handleSubmitQuiz}
                  className="px-4 py-1.5 rounded-lg bg-mint text-canvas font-semibold text-xs hover:brightness-110 transition cursor-pointer"
                >
                  Submit Quiz ({Object.keys(selectedAnswers).length}/{activeQuestions.length})
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
                    onClick={handleResetAll}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg border border-line bg-canvas text-xs font-mono text-ink hover:border-mint transition cursor-pointer"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    Restart Full Quiz
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
