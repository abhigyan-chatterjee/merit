import React, { useEffect, useRef, useState } from 'react';
import { Link, useParams, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, ListChecks, BrainCircuit } from 'lucide-react';
import { TARGETED_EXAMS } from '../data/exams';
import { ExamMcqSection } from '../components/ExamMcqSection';
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
  const [secondsRemaining, setSecondsRemaining] = useState(exam?.durationSec ?? 0);
  const [examSubmitted, setExamSubmitted] = useState(false);
  const [isAutoSubmitRequested, setIsAutoSubmitRequested] = useState(false);
  const [proctorNotice, setProctorNotice] = useState<string | null>(null);
  const [warningCount, setWarningCount] = useState(0);
  const warningsRef = useRef(0);

  useEffect(() => {
    setStarted(false);
    setMcqPct(null);
    setCodingPassed({});
    setSelectedItem({ type: 'mcq', index: 0 });
    setAnsweredMcqs({});
    setLoadedMcqCount(0);
    setMcqQuestionIds([]);
    setExamSubmitted(false);
    setIsAutoSubmitRequested(false);
    setProctorNotice(null);
    setWarningCount(0);
    warningsRef.current = 0;

    try {
      const raw = sessionStorage.getItem(`merit_exam_${id}`);
      if (raw) {
        const data = JSON.parse(raw);
        const now = Date.now();
        if (data.started && data.endAtMs > now) {
          setStarted(true);
          setSecondsRemaining(Math.max(0, Math.ceil((data.endAtMs - now) / 1000)));
          if (typeof data.warnings === 'number') {
            setWarningCount(data.warnings);
            warningsRef.current = data.warnings;
          }
          return;
        } else if (data.started) {
          sessionStorage.removeItem(`merit_exam_${id}`);
        }
      }
    } catch {
      // sessionStorage unavailable
    }
    setSecondsRemaining(exam?.durationSec ?? 0);
  }, [id, exam?.durationSec]);

  const handleStartExam = () => {
    const duration = exam?.durationSec ?? 0;
    const endAtMs = Date.now() + duration * 1000;
    try {
      sessionStorage.setItem(
        `merit_exam_${id}`,
        JSON.stringify({ started: true, endAtMs, warnings: 0 })
      );
    } catch {
      // sessionStorage unavailable
    }
    setSecondsRemaining(duration);
    warningsRef.current = 0;
    setWarningCount(0);
    setStarted(true);
  };

  useEffect(() => {
    if (examSubmitted) {
      try {
        sessionStorage.removeItem(`merit_exam_${id}`);
      } catch {
        // sessionStorage unavailable
      }
    }
  }, [examSubmitted, id]);

  useEffect(() => {
    if (!started || examSubmitted) return;
    const timer = window.setInterval(() => {
      setSecondsRemaining((remaining) => Math.max(remaining - 1, 0));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [started, examSubmitted]);

  useEffect(() => {
    if (!started || examSubmitted || secondsRemaining > 0) return;
    setIsAutoSubmitRequested(true);
  }, [started, examSubmitted, secondsRemaining]);

  useEffect(() => {
    warningsRef.current = warningCount;
  }, [warningCount]);

  useEffect(() => {
    if (!started || examSubmitted) return;
    const handleSwitch = () => {
      const next = warningsRef.current + 1;
      warningsRef.current = next;
      setWarningCount(next);
      try {
        const raw = sessionStorage.getItem(`merit_exam_${id}`);
        if (raw) {
          const data = JSON.parse(raw);
          sessionStorage.setItem(`merit_exam_${id}`, JSON.stringify({ ...data, warnings: next }));
        }
      } catch {
        // sessionStorage unavailable
      }
      if (next >= 3) {
        setIsAutoSubmitRequested(true);
        setProctorNotice('Exam auto-submitted: tab switch or window blur detected.');
      } else {
        setProctorNotice(
          `Warning ${next} of 2: Tab switch or window blur detected. On the 3rd event, the exam will auto-submit.`
        );
      }
    };
    const handleVisibilityChange = () => {
      if (document.hidden) {
        handleSwitch();
      }
    };
    const handleBlur = () => {
      handleSwitch();
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('blur', handleBlur);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('blur', handleBlur);
    };
  }, [started, examSubmitted, id]);

  const formatTime = (seconds: number) =>
    `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, '0')}`;

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
        <Link to="/exams" className="inline-block py-1.5 hover:text-mint transition-colors">
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
            {Math.round(exam.durationSec / 60)}-minute countdown · Leaving the tab or window gives 2 warnings; on the 3rd, the exam auto-submits · unanswered questions count as
            wrong. The timer auto-submits at zero.
          </p>
          {user ? (
            <button
              onClick={handleStartExam}
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
          <div className="sticky top-16 z-30 flex justify-end">
            <div
              aria-label={`Time remaining ${formatTime(secondsRemaining)}`}
              className={`inline-flex items-center rounded-lg border px-3 py-1.5 font-mono text-sm font-bold shadow-sm ${
                secondsRemaining < 60
                  ? 'border-rose/60 bg-rose/15 text-rose animate-pulse'
                  : secondsRemaining < 300
                    ? 'border-amber/60 bg-amber/15 text-amber'
                    : 'border-line bg-surface text-ink'
              }`}
            >
              ⏱ {formatTime(secondsRemaining)}
            </div>
          </div>
          {proctorNotice && (
            <div role="alert" className="rounded-lg border border-rose/50 bg-rose/10 px-3 py-2 text-xs font-mono text-rose">
              {proctorNotice}
            </div>
          )}
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
            <div className="min-w-0">
              <div
                hidden={selectedItem.type !== 'mcq'}
              >
                <ExamMcqSection
                  key={exam.id}
                  examId={exam.id}
                  examTitle={exam.title}
                  topics={exam.topics}
                  questionCount={exam.questionCount}
                  difficulty={exam.difficulty ?? ''}
                  topicPlan={exam.topicPlan}
                  durationSec={exam.durationSec}
                  currentIndex={selectedItem.index}
                  onCurrentIndexChange={(index) => setSelectedItem({ type: 'mcq', index })}
                  onAnswersChange={(answers) =>
                    setAnsweredMcqs(Object.fromEntries(Object.keys(answers).map((questionId) => [questionId, true])))
                  }
                  onQuestionIdsChange={(ids) => {
                    setMcqQuestionIds(ids);
                    setLoadedMcqCount(ids.length);
                  }}
                  onComplete={(pct) => {
                    if (exam.coding.length === 0) {
                      setExamSubmitted(true);
                    }
                    setMcqPct(pct);
                    saveQuizScore(`exam:${exam.id}`, pct);
                  }}
                  isAutoSubmitRequested={isAutoSubmitRequested}
                />
              </div>
              {exam.coding.length > 0 && selectedItem.type === 'coding' && (
                <ExamCodingSection
                  coding={exam.coding}
                  selectedSlug={exam.coding[selectedItem.index]?.slug}
                  onVerdict={(slug, passed) => setCodingPassed((prev) => ({ ...prev, [slug]: passed }))}
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
