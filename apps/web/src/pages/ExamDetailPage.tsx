import React, { useState } from 'react';
import { Link, useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, ListChecks, BrainCircuit } from 'lucide-react';
import { TARGETED_EXAMS } from '../data/exams';
import { QuizEngine } from '../components/QuizEngine';
import { ExamCodingSection } from '../components/ExamCodingSection';
import { useProgress } from '../store/ProgressContext';
import { useAuth } from '../store/AuthContext';
import { NotFound } from '../components/NotFound';

export const ExamDetailPage: React.FC = () => {
  const { id = '' } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { saveQuizScore } = useProgress();
  const { user, isLoading: authLoading } = useAuth();
  const currentPath = `${location.pathname}${location.search}${location.hash}`;
  const loginNext = currentPath.startsWith('/') ? currentPath : '/exams';

  const exam = TARGETED_EXAMS.find((e) => e.id === id);
  const [started, setStarted] = useState(false);
  const [mcqPct, setMcqPct] = useState<number | null>(null);
  const [codingPassed, setCodingPassed] = useState<Record<string, boolean>>({});
  const [selectedItem, setSelectedItem] = useState<{ type: 'mcq' | 'coding'; index: number }>({
    type: 'mcq',
    index: 0,
  });
  const [answeredMcqs, setAnsweredMcqs] = useState<Record<string, boolean>>({});
  const [loadedMcqCount, setLoadedMcqCount] = useState(0);
  const [mcqQuestionIds, setMcqQuestionIds] = useState<string[]>([]);

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

  const selectMcq = (targetIndex: number) => {
    setSelectedItem({ type: 'mcq', index: targetIndex });
  };

  const items = [
    ...Array.from({ length: exam.questionCount }, (_, index) => ({
      type: 'mcq' as const,
      index,
      label: `Question ${index + 1}`,
      answered: !!answeredMcqs[mcqQuestionIds[index]],
    })),
    ...exam.coding.map((item, index) => ({
      type: 'coding' as const,
      index,
      label: item.title,
      answered: !!codingPassed[item.slug],
      slug: item.slug,
    })),
  ];

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
          {user ? (
            <button
              onClick={() => setStarted(true)}
              className="px-5 py-2.5 rounded-lg bg-violet text-canvas font-semibold text-xs hover:brightness-110 transition cursor-pointer"
            >
              Start timed exam
            </button>
          ) : authLoading ? null : (
            <Link
              to={`/login?next=${encodeURIComponent(loginNext)}`}
              className="inline-flex items-center justify-center gap-1.5 px-5 py-2.5 rounded-lg bg-violet text-canvas font-semibold text-xs hover:brightness-110 transition cursor-pointer"
            >
              Sign in to start exam
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-6">
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
          {loadedMcqCount > 0 && loadedMcqCount < exam.questionCount && (
            <div role="status" className="rounded-lg border border-amber/40 bg-amber/10 px-3 py-2 text-xs text-amber">
              This exam loaded {loadedMcqCount} of {exam.questionCount} MCQs. Some questions are unavailable right now.
            </div>
          )}
          <div className="md:hidden">
            <label htmlFor="exam-question-select" className="sr-only">Select exam question</label>
            <select
              id="exam-question-select"
              value={`${selectedItem.type}-${selectedItem.index}`}
              onChange={(event) => {
                const [type, index] = event.target.value.split('-');
                if (type === 'mcq') selectMcq(Number(index));
                else setSelectedItem({ type: 'coding', index: Number(index) });
              }}
              className="w-full rounded-lg border border-line bg-surface px-3 py-2 text-xs font-mono text-ink"
            >
              <option disabled>MCQs ({exam.questionCount})</option>
              {items.filter((item) => item.type === 'mcq').map((item) => (
                <option key={`mcq-${item.index}`} value={`mcq-${item.index}`}>
                  {item.label} · {item.answered ? 'answered' : 'unanswered'}
                </option>
              ))}
              {exam.coding.length > 0 && <option disabled>Coding ({exam.coding.length})</option>}
              {items.filter((item) => item.type === 'coding').map((item) => (
                <option key={`coding-${item.index}`} value={`coding-${item.index}`}>
                  {item.label} · {item.answered ? 'Accepted' : 'unattempted'}
                </option>
              ))}
            </select>
          </div>
          <div className="grid gap-6 md:grid-cols-[13rem_1fr] items-start">
            <aside className="hidden md:block rounded-xl border border-line bg-surface p-3 space-y-3">
              <h2 className="text-xs font-bold text-ink">Exam navigator</h2>
              <div>
                <h3 className="px-2 pb-1 text-[10px] font-mono uppercase tracking-wider text-muted">
                  MCQs ({exam.questionCount})
                </h3>
                <div className="space-y-1">
                  {items.filter((item) => item.type === 'mcq').map((item) => (
                    <button
                      key={`mcq-${item.index}`}
                      onClick={() => selectMcq(item.index)}
                      className={`w-full flex items-center justify-between gap-2 rounded px-2 py-1.5 text-left text-[11px] font-mono cursor-pointer ${
                        selectedItem.type === 'mcq' && selectedItem.index === item.index
                          ? 'bg-violet/15 text-violet'
                          : 'text-ink hover:bg-canvas'
                      }`}
                    >
                      <span className="truncate">{item.label}</span>
                      <span aria-label={item.answered ? 'answered' : 'unanswered'} className={item.answered ? 'text-mint' : 'text-muted'}>
                        {item.answered ? '●' : '○'}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
              {exam.coding.length > 0 && (
                <div>
                  <h3 className="px-2 pb-1 text-[10px] font-mono uppercase tracking-wider text-muted">
                    Coding ({exam.coding.length})
                  </h3>
                  <div className="space-y-1">
                    {items.filter((item) => item.type === 'coding').map((item) => (
                      <button
                        key={`coding-${item.index}`}
                        onClick={() => setSelectedItem({ type: 'coding', index: item.index })}
                        className={`w-full flex items-center justify-between gap-2 rounded px-2 py-1.5 text-left text-[11px] font-mono cursor-pointer ${
                          selectedItem.type === 'coding' && selectedItem.index === item.index
                            ? 'bg-violet/15 text-violet'
                            : 'text-ink hover:bg-canvas'
                        }`}
                      >
                        <span className="truncate">{item.label}</span>
                        <span aria-label={item.answered ? 'Accepted' : 'unattempted'} className={item.answered ? 'text-mint' : 'text-muted'}>
                          {item.answered ? '●' : '○'}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </aside>
            <main>
              <div
                hidden={selectedItem.type !== 'mcq'}
              >
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
                  currentIndex={selectedItem.index}
                  onCurrentIndexChange={(index) => setSelectedItem({ type: 'mcq', index })}
                  onAnswersChange={(answers) =>
                    setAnsweredMcqs(Object.fromEntries(Object.keys(answers).map((questionId) => [questionId, true])))
                  }
                  onQuestionCountChange={setLoadedMcqCount}
                  onQuestionIdsChange={setMcqQuestionIds}
                  onComplete={(pct) => {
                    setMcqPct(pct);
                    saveQuizScore(`exam:${exam.id}`, pct);
                  }}
                />
              </div>
              {exam.coding.length > 0 && selectedItem.type === 'coding' && (
                <ExamCodingSection
                  coding={exam.coding}
                  selectedSlug={exam.coding[selectedItem.index]?.slug}
                  onVerdict={(slug, passed) => setCodingPassed((prev) => ({ ...prev, [slug]: passed }))}
                />
              )}
            </main>
          </div>
        </div>
      )}
    </div>
  );
};
