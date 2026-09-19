import React, { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, ListChecks, BrainCircuit } from 'lucide-react';
import { TARGETED_EXAMS } from '../data/exams';
import { QuizEngine } from '../components/QuizEngine';
import { ExamCodingSection } from '../components/ExamCodingSection';
import { useProgress } from '../store/ProgressContext';
import { NotFound } from '../components/NotFound';

export const ExamDetailPage: React.FC = () => {
  const { id = '' } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { saveQuizScore } = useProgress();

  const exam = TARGETED_EXAMS.find((e) => e.id === id);
  const [started, setStarted] = useState(false);
  const [mcqPct, setMcqPct] = useState<number | null>(null);
  const [codingPassed, setCodingPassed] = useState<Record<string, boolean>>({});

  if (!exam) {
    return (
      <NotFound
        title="Exam Not Found"
        message={`We couldn't find an exam for "${id}". Pick one from the exams catalog.`}
        backTo="/exams"
        backLabel="All Exams"
      />
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 space-y-6">
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-[10px] font-mono text-muted">
        <Link to="/exams" className="hover:text-mint transition-colors">
          exams
        </Link>
        <span>/</span>
        <span className="text-ink">{exam.id}</span>
      </nav>

      <div className="flex flex-wrap items-start justify-between gap-4 pb-4 border-b border-line">
        <div className="space-y-1.5 min-w-0">
          <h1 className="text-2xl font-bold tracking-tight text-ink flex items-center gap-2.5">
            <BrainCircuit className="w-6 h-6 text-violet" />
            {exam.title}
          </h1>
          <p className="text-xs text-muted">{exam.description}</p>
          <div className="flex items-center gap-4 text-[11px] font-mono text-muted pt-1">
            <span className="inline-flex items-center gap-1.5">
              <ListChecks className="w-3.5 h-3.5 text-mint" />
              {exam.questionCount} MCQs
              {exam.coding.length > 0 && ` · ${exam.coding.length} coding`} ·{' '}
              {Math.round(exam.durationSec / 60)} min · auto-submits
            </span>
          </div>
        </div>
        <button
          onClick={() => navigate('/exams')}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-line bg-surface text-xs font-mono text-muted hover:text-ink transition cursor-pointer"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          All exams
        </button>
      </div>

      {!started ? (
        <div className="p-6 rounded-xl border border-line bg-surface space-y-4 text-center">
          <p className="text-sm text-ink font-semibold">Ready when you are.</p>
          <p className="text-xs text-muted max-w-lg mx-auto">
            {exam.questionCount} MCQs
            {exam.coding.length > 0 && ` · ${exam.coding.length} coding questions`} ·{' '}
            {Math.round(exam.durationSec / 60)}-minute countdown · unanswered questions count as
            wrong. The timer auto-submits at zero.
          </p>
          <button
            onClick={() => setStarted(true)}
            className="px-5 py-2.5 rounded-lg bg-violet text-canvas font-semibold text-xs hover:brightness-110 transition cursor-pointer"
          >
            Start timed exam
          </button>
        </div>
      ) : (
        <div className="space-y-10">
          {(mcqPct !== null || Object.keys(codingPassed).length > 0) && (
            <div className="p-4 rounded-xl border border-mint/40 bg-mint/5 text-xs font-mono text-ink">
              MCQ score: {mcqPct ?? '—'}%
              {exam.coding.length > 0 && (
                <>
                  {' '}· Coding accepted:{' '}
                  {Object.values(codingPassed).filter(Boolean).length}/{exam.coding.length}
                </>
              )}
            </div>
          )}
          <QuizEngine
            key={exam.id}
            topicTitle={exam.title}
            topicId="mixed"
            examTopics={exam.topics}
            examCount={exam.questionCount}
            examDifficulty={exam.difficulty}
            examTopicPlan={exam.topicPlan}
            isMock
            perQuestionSec={null}
            durationLimitSec={exam.durationSec}
            onComplete={(pct) => {
              setMcqPct(pct);
              saveQuizScore(`exam:${exam.id}`, pct);
            }}
          />
          {exam.coding.length > 0 && (
            <ExamCodingSection
              coding={exam.coding}
              onVerdict={(slug, passed) => setCodingPassed((prev) => ({ ...prev, [slug]: passed }))}
            />
          )}
        </div>
      )}
    </div>
  );
};
