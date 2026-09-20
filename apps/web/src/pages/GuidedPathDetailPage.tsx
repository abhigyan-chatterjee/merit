import React, { useState, useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  LayoutGrid,
  GitCommit,
  Network,
  Cpu,
  ChevronRight,
  Layers,
  Code2,
  BrainCircuit,
  ClipboardCheck,
  Check,
  ArrowRight,
} from 'lucide-react';
import { LEARNING_PATHS, PathStep } from '../data/learningPaths';
import { resolveStep } from '../utils/stepLink';
import { useProgress } from '../store/ProgressContext';
import { useAuth } from '../store/AuthContext';
import { contentApi } from '../utils/api';
import { NotFound } from '../components/NotFound';

const PATH_ICONS: Record<string, React.ComponentType<any>> = {
  LayoutGrid,
  GitCommit,
  Network,
  Cpu,
};
const STEP_ICONS: Record<PathStep['type'], React.ComponentType<any>> = {
  visualizer: Layers,
  problem: Code2,
  quiz: BrainCircuit,
  mock: ClipboardCheck,
};
const STEP_TONE: Record<PathStep['type'], string> = {
  visualizer: 'text-mint',
  problem: 'text-violet',
  quiz: 'text-amber',
  mock: 'text-amber',
};
const STEP_LABEL: Record<PathStep['type'], string> = {
  visualizer: 'Workbench',
  problem: 'Problem',
  quiz: 'Quiz',
  mock: 'Mock',
};

interface ServerPathData {
  slug: string;
  title: string;
  blurb: string;
  icon: string;
  track: string;
  ordinal: number;
  total_steps: number;
  completed_steps: number;
  progress_pct: number;
  next_step_id: number | null;
  steps: Array<{
    id: number;
    ordinal: number;
    step_type: string;
    ref_id: string;
    title: string | null;
    summary: string | null;
    reading_links: string[];
    completed: boolean;
  }>;
}

export const GuidedPathDetailPage: React.FC = () => {
  const { id = 'foundation' } = useParams<{ id: string }>();
  const { state } = useProgress();
  const { user } = useAuth();

  const [serverPath, setServerPath] = useState<ServerPathData | null>(null);

  useEffect(() => {
    // No authenticated user: skip the fetch entirely so cards and the
    // detail header share one local counting rule (4/8 = 50% everywhere).
    if (!user) {
      setServerPath(null);
      return;
    }
    let active = true;
    contentApi
      .getPath(id)
      .then((data) => {
        if (active && data) {
          setServerPath(data);
        }
      })
      .catch(() => {
        // Fallback to local
      });
    return () => {
      active = false;
    };
  }, [id, user]);

  const fallbackPath = LEARNING_PATHS.find((p) => p.id === id);

  if (!fallbackPath && !serverPath) {
    return (
      <NotFound
        title="Learning Path Not Found"
        message={`The learning path "${id}" does not exist.`}
        backTo="/paths"
        backLabel="All Guided Paths"
      />
    );
  }

  const title = serverPath?.title || fallbackPath?.title || id;
  const blurb = serverPath?.blurb || fallbackPath?.blurb || '';
  const iconName = serverPath?.icon || fallbackPath?.icon || 'LayoutGrid';
  const Icon = PATH_ICONS[iconName] ?? LayoutGrid;

  // Build steps list
  let steps: PathStep[] = [];
  let stepStatus: Array<{ done: boolean; next: boolean }> = [];

  if (serverPath && serverPath.steps.length > 0) {
    steps = serverPath.steps.map((s) => ({
      type: s.step_type as PathStep['type'],
      id: s.ref_id,
      title: s.title || undefined,
      summary: s.summary || undefined,
      readingLinks: s.reading_links?.length ? s.reading_links : undefined,
    }));

    stepStatus = serverPath.steps.map((s) => {
      let done = s.completed;
      const stepType = s.step_type;
      if (stepType === 'problem') {
        done = done || state.progress[s.ref_id] === 'Done';
      } else if (stepType === 'quiz' || stepType === 'mock') {
        done = done || (state.quizzes[s.ref_id] ?? 0) >= 70;
      } else if (stepType === 'visualizer') {
        done = done || (state.visitedVisualizers?.includes(s.ref_id) ?? false);
      }
      return { done, next: false };
    });

    const firstIncomplete = stepStatus.findIndex((s) => !s.done);
    if (firstIncomplete !== -1) {
      stepStatus[firstIncomplete].next = true;
    }
  } else if (fallbackPath) {
    steps = fallbackPath.steps;
    stepStatus = fallbackPath.steps.map((step): { done: boolean; next: boolean } => {
      let done = false;
      if (step.type === 'problem') {
        done = state.progress[step.id] === 'Done';
      } else if (step.type === 'quiz' || step.type === 'mock') {
        done = (state.quizzes[step.id] ?? 0) >= 70;
      } else if (step.type === 'visualizer') {
        done = state.visitedVisualizers?.includes(step.id) ?? false;
      }
      return { done, next: false };
    });

    const firstIncomplete = stepStatus.findIndex((s) => !s.done);
    if (firstIncomplete !== -1) stepStatus[firstIncomplete].next = true;
  }

  const doneCount = stepStatus.filter((s) => s.done).length;
  const pct =
    serverPath != null
      ? serverPath.progress_pct
      : steps.length > 0
      ? Math.round((doneCount / steps.length) * 100)
      : 0;

  const nextIndex = stepStatus.findIndex((s) => s.next);
  const nextStep = nextIndex !== -1 ? steps[nextIndex] : null;
  const nextResolved = nextStep ? resolveStep(nextStep) : null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-[10px] font-mono text-muted">
        <Link to="/learn" className="hover:text-mint transition-colors">
          learning paths
        </Link>
        <ChevronRight className="w-3 h-3" />
        <span className="text-ink">{id}</span>
      </nav>

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-5 pb-6 border-b border-line">
        <div className="flex items-start gap-4 min-w-0">
          <div className="w-12 h-12 rounded-xl border border-line bg-surface grid place-items-center text-mint shrink-0">
            <Icon className="w-6 h-6" />
          </div>
          <div className="min-w-0 space-y-1.5">
            <h1 className="text-2xl font-bold tracking-tight text-ink">{title}</h1>
            <p className="text-xs text-muted">{blurb}</p>
          </div>
        </div>

        <div className="text-right shrink-0">
          <div className="text-3xl font-bold font-mono tracking-tighter tnum text-mint">{pct}%</div>
          <div className="text-[10px] font-mono text-muted">
            {doneCount}/{steps.length} complete
          </div>
        </div>
      </div>

      {/* Next step CTA */}
      {nextResolved && (
        <Link
          to={`${nextResolved.link}?path=${id}&step=${nextIndex}`}
          className="group flex items-center gap-4 p-4 rounded-xl border border-mint/40 bg-mint/5 hover:bg-mint/10 transition-colors"
        >
          <div className="w-9 h-9 rounded-lg bg-mint grid place-items-center text-canvas shrink-0">
            <ArrowRight className="w-4 h-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[10px] font-mono uppercase tracking-[0.16em] text-mint">
              Next up · {STEP_LABEL[nextStep!.type]}
            </div>
            <div className="text-sm font-semibold text-ink truncate">{nextResolved.title}</div>
          </div>
          <ChevronRight className="w-4 h-4 text-mint group-hover:translate-x-0.5 transition-transform shrink-0" />
        </Link>
      )}

      {/* Step list */}
      <ol className="relative space-y-0">
        {steps.map((step, i) => {
          const resolved = resolveStep(step);
          const status = stepStatus[i] || { done: false, next: false };
          const StepIcon = STEP_ICONS[step.type] || Code2;
          const tone = STEP_TONE[step.type] || 'text-mint';

          return (
            <li key={`${step.type}-${step.id}-${i}`} className="relative flex gap-4 pb-2">
              {/* connector rail */}
              {i < steps.length - 1 && (
                <span
                  className="absolute left-[15px] top-9 bottom-0 w-px bg-line"
                  aria-hidden="true"
                />
              )}

              {/* node */}
              <div
                className={`relative z-10 w-8 h-8 rounded-lg border grid place-items-center shrink-0 ${
                  status.done
                    ? 'bg-mint border-mint text-canvas'
                    : status.next
                    ? 'bg-surface border-mint text-mint ring-2 ring-mint/30'
                    : 'bg-surface border-line text-muted hover:border-steel'
                }`}
              >
                {status.done ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <StepIcon className="w-4 h-4" />
                )}
              </div>

              {/* step body */}
              <div className="flex-1 min-w-0 pb-4">
                <Link
                  to={`${resolved.link}?path=${id}&step=${i}`}
                  className="block group"
                >
                  <div className="flex items-baseline gap-3 min-w-0">
                    <span className="font-mono text-[10px] text-muted/60 tnum shrink-0">
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-[9px] font-mono uppercase tracking-[0.16em] ${tone}`}>
                          {STEP_LABEL[step.type] || 'Step'}
                        </span>
                        {status.done && (
                          <span className="text-[9px] font-mono text-mint">✓ done</span>
                        )}
                        {status.next && (
                          <span className="text-[9px] font-mono text-mint bg-mint/10 px-1.5 py-0.5 rounded font-semibold">
                            current
                          </span>
                        )}
                      </div>
                      <span
                        className={`text-sm font-semibold group-hover:text-mint transition-colors ${
                          status.done ? 'text-muted' : status.next ? 'text-mint font-bold' : 'text-ink'
                        }`}
                      >
                        {resolved.title}
                      </span>
                      <div className="text-[10px] font-mono text-muted">{resolved.subtitle}</div>
                      {step.summary && (
                        <p className="text-xs text-muted leading-relaxed mt-1">{step.summary}</p>
                      )}
                      {step.readingLinks && step.readingLinks.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-1.5">
                          {step.readingLinks.map((url) => (
                            <a
                              key={url}
                              href={url}
                              target="_blank"
                              rel="noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="text-[10px] font-mono text-mint hover:underline"
                            >
                              Further reading →
                            </a>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </Link>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
};
