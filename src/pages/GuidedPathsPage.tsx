import React from 'react';
import { Link } from 'react-router-dom';
import { LayoutGrid, GitCommit, Network, Cpu, ChevronRight } from 'lucide-react';
import { LEARNING_PATHS } from '../data/learningPaths';
import { resolveStep } from '../utils/stepLink';
import { useProgress } from '../store/ProgressContext';
import { Reveal } from '../components/ui/Reveal';

const PATH_ICONS: Record<string, React.ComponentType<any>> = {
  LayoutGrid,
  GitCommit,
  Network,
  Cpu
};

function usePathProgress(pathId: string): { done: number; total: number; pct: number } {
  const { state } = useProgress();
  let done = 0;
  let total = 0;
  const path = LEARNING_PATHS.find((p) => p.id === pathId);
  if (path) {
    for (const step of path.steps) {
      total++;
      if (step.type === 'problem') {
        if (state.progress[step.id] === 'Done') done++;
      } else if (step.type === 'quiz') {
        if ((state.quizzes[step.id] ?? 0) >= 70) done++;
      }
      // visualizers are counted by simply having been stepped-through via lastVisited
      else if (step.type === 'visualizer' && state.lastVisited?.path === `/visualizers/${step.id}`) {
        done++;
      }
    }
  }
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  return { done, total, pct };
}

const PathCard: React.FC<{ pathId: string; index: number }> = ({ pathId, index }) => {
  const path = LEARNING_PATHS.find((p) => p.id === pathId)!;
  const Icon = PATH_ICONS[path.icon] ?? LayoutGrid;
  const { done, total, pct } = usePathProgress(path.id);
  const preview = path.steps.slice(0, 3).map((s) => resolveStep(s).title);
  const complete = pct === 100;
  const recommended = path.id === 'foundations';

  return (
    <Reveal delay={index * 0.05}>
      <Link
        to={`/learn/${path.id}`}
        className={`bracketed group relative block h-full rounded-xl border bg-surface transition-colors duration-200 ${
          recommended ? 'border-mint/50 hover:border-mint' : 'border-line hover:border-steel'
        }`}
      >
        {recommended && (
          <span className="absolute -top-2 left-4 px-1.5 py-0.5 rounded bg-mint text-canvas text-[9px] font-mono uppercase tracking-widest">
            Start here
          </span>
        )}
        <div className="p-5 space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-lg border border-line bg-canvas grid place-items-center text-mint shrink-0">
                <Icon className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <h2 className="text-sm font-bold text-ink group-hover:text-mint transition-colors truncate">
                  {path.title}
                </h2>
                <p className="text-[10px] font-mono text-muted">
                  {path.steps.length} steps · {done}/{total} complete
                </p>
              </div>
            </div>
            <ChevronRight className="w-4 h-4 text-muted group-hover:text-mint transition-colors shrink-0" />
          </div>

          <p className="text-xs text-muted leading-relaxed">{path.blurb}</p>

          <div className="flex flex-wrap gap-1.5">
            {preview.map((t) => (
              <span
                key={t}
                className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-canvas border border-line text-muted"
              >
                {t}
              </span>
            ))}
            {path.steps.length > 3 && (
              <span className="text-[10px] font-mono text-muted">
                +{path.steps.length - 3} more
              </span>
            )}
          </div>

          <div className="space-y-1.5">
            <div className="flex items-center justify-between text-[10px] font-mono text-muted">
              <span>{complete ? 'Complete' : 'Progress'}</span>
              <span className={complete ? 'text-mint' : 'text-ink'}>{pct}%</span>
            </div>
            <span className="block h-1.5 rounded-full bg-line overflow-hidden">
              <span
                className="block h-full bg-mint transition-all duration-300"
                style={{ width: `${pct}%` }}
              />
            </span>
          </div>
        </div>
      </Link>
    </Reveal>
  );
};

export const GuidedPathsPage: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="space-y-1.5">
        <span className="text-[10px] font-mono uppercase tracking-[0.2em] text-mint">
          Guided paths
        </span>
        <h1 className="text-2xl font-bold tracking-tight text-ink">Learning paths</h1>
        <p className="text-xs text-muted max-w-2xl">
          Structured routes that mix workbenches, problems and quizzes in a recommended order.
          Follow the line, check things off as you go.
        </p>
      </div>

      {/* Path cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {LEARNING_PATHS.map((path, i) => (
          <PathCard key={path.id} pathId={path.id} index={i} />
        ))}
      </div>
    </div>
  );
};
