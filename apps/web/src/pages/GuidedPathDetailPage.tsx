import React from 'react';
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
  Check,
  Lock,
  ArrowRight
} from 'lucide-react';
import { LEARNING_PATHS, PathStep } from '../data/learningPaths';
import { resolveStep } from '../utils/stepLink';
import { useProgress } from '../store/ProgressContext';

const PATH_ICONS: Record<string, React.ComponentType<any>> = { LayoutGrid, GitCommit, Network, Cpu };
const STEP_ICONS: Record<PathStep['type'], React.ComponentType<any>> = {
  visualizer: Layers,
  problem: Code2,
  quiz: BrainCircuit
};
const STEP_TONE: Record<PathStep['type'], string> = {
  visualizer: 'text-mint',
  problem: 'text-violet',
  quiz: 'text-amber'
};
const STEP_LABEL: Record<PathStep['type'], string> = {
  visualizer: 'Workbench',
  problem: 'Problem',
  quiz: 'Quiz'
};

export const GuidedPathDetailPage: React.FC = () => {
  const { id = 'foundations' } = useParams<{ id: string }>();
  const { state } = useProgress();

  const path = LEARNING_PATHS.find((p) => p.id === id) || LEARNING_PATHS[0];
  const Icon = PATH_ICONS[path.icon] ?? LayoutGrid;

  // Compute per-step completion
  const stepStatus = path.steps.map((step): { done: boolean; next: boolean } => {
    let done = false;
    if (step.type === 'problem') {
      done = state.progress[step.id] === 'Done';
    } else if (step.type === 'quiz') {
      done = (state.quizzes[step.id] ?? 0) >= 70;
    } else if (step.type === 'visualizer') {
      done = state.lastVisited?.path === `/visualizers/${step.id}`;
    }
    return { done, next: false };
  });

  // First incomplete step is "next"
  const firstIncomplete = stepStatus.findIndex((s) => !s.done);
  if (firstIncomplete !== -1) stepStatus[firstIncomplete].next = true;

  const doneCount = stepStatus.filter((s) => s.done).length;
  const pct = path.steps.length > 0 ? Math.round((doneCount / path.steps.length) * 100) : 0;
  const nextStep = firstIncomplete !== -1 ? path.steps[firstIncomplete] : null;
  const nextResolved = nextStep ? resolveStep(nextStep) : null;

  return (
    <div className="max-w-4xl mx-auto px-4 py-8 space-y-8">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-[10px] font-mono text-muted">
        <Link to="/learn" className="hover:text-mint transition-colors">
          learning paths
        </Link>
        <ChevronRight className="w-3 h-3" />
        <span className="text-ink">{path.id}</span>
      </nav>

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-5 pb-6 border-b border-line">
        <div className="flex items-start gap-4 min-w-0">
          <div className="w-12 h-12 rounded-xl border border-line bg-surface grid place-items-center text-mint shrink-0">
            <Icon className="w-6 h-6" />
          </div>
          <div className="min-w-0 space-y-1.5">
            <h1 className="text-2xl font-bold tracking-tight text-ink">{path.title}</h1>
            <p className="text-xs text-muted">{path.blurb}</p>
          </div>
        </div>

        <div className="text-right shrink-0">
          <div className="text-3xl font-bold font-mono tracking-tighter tnum text-mint">{pct}%</div>
          <div className="text-[10px] font-mono text-muted">{doneCount}/{path.steps.length} complete</div>
        </div>
      </div>

      {/* Next step CTA */}
      {nextResolved && (
        <Link
          to={nextResolved.link}
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
        {path.steps.map((step, i) => {
          const resolved = resolveStep(step);
          const status = stepStatus[i];
          const StepIcon = STEP_ICONS[step.type];
          const tone = STEP_TONE[step.type];
          const isLocked = !status.done && !status.next;

          return (
            <li key={`${step.type}-${step.id}-${i}`} className="relative flex gap-4 pb-2">
              {/* connector rail */}
              {i < path.steps.length - 1 && (
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
                    ? 'bg-surface border-mint text-mint'
                    : 'bg-surface border-line text-muted/60'
                }`}
              >
                {status.done ? (
                  <Check className="w-4 h-4" />
                ) : isLocked ? (
                  <Lock className="w-3 h-3" />
                ) : (
                  <StepIcon className="w-4 h-4" />
                )}
              </div>

              {/* step body */}
              <div className="flex-1 min-w-0 pb-4">
                <Link
                  to={resolved.link}
                  className={isLocked ? 'pointer-events-none' : 'block'}
                  aria-disabled={isLocked}
                >
                  <div className="flex items-baseline gap-3 min-w-0">
                    <span className="font-mono text-[10px] text-muted/60 tnum shrink-0">
                      {String(i + 1).padStart(2, '0')}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-[9px] font-mono uppercase tracking-[0.16em] ${tone}`}>
                          {STEP_LABEL[step.type]}
                        </span>
                        {status.done && (
                          <span className="text-[9px] font-mono text-mint">✓ done</span>
                        )}
                      </div>
                      <span
                        className={`text-sm font-semibold ${
                          isLocked ? 'text-muted/60' : status.done ? 'text-muted' : 'text-ink'
                        }`}
                      >
                        {resolved.title}
                      </span>
                      <div className="text-[10px] font-mono text-muted">{resolved.subtitle}</div>
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
