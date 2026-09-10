import React, { useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowLeft,
  ArrowRight,
  ChevronDown,
  CheckCircle2,
  Layers,
  Code2,
  BrainCircuit,
} from 'lucide-react';
import { LEARNING_PATHS } from '../data/learningPaths';
import { resolveStep } from '../utils/stepLink';
import { useProgress } from '../store/ProgressContext';
import { useAuth } from '../store/AuthContext';
import { progressApi } from '../utils/api';

interface LessonNavProps {
  currentType: 'visualizer' | 'problem' | 'quiz';
  currentId: string;
}

const STEP_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  visualizer: Layers,
  problem: Code2,
  quiz: BrainCircuit,
};

export const LessonNav: React.FC<LessonNavProps> = ({ currentType, currentId }) => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { state, recordVisualizerVisit } = useProgress();
  const { user } = useAuth();
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Only show path navigation when the user arrived through a path
  // (links from path pages carry ?path=<id>&step=<n>). Standalone visits
  // to a workbench / problem / quiz must not show path UI.
  const pathParam = searchParams.get('path');
  const stepParam = searchParams.get('step');
  const matchedPath = pathParam ? LEARNING_PATHS.find((p) => p.id === pathParam) ?? null : null;

  if (!matchedPath || stepParam === null) {
    return null;
  }

  const steps = matchedPath.steps;
  const currentStepIndex = steps.findIndex(
    (s) => s.type === currentType && s.id === currentId
  );

  const prevStep = currentStepIndex > 0 ? steps[currentStepIndex - 1] : null;
  const nextStep =
    currentStepIndex >= 0 && currentStepIndex < steps.length - 1
      ? steps[currentStepIndex + 1]
      : null;

  const currentResolved =
    currentStepIndex >= 0 ? resolveStep(steps[currentStepIndex]) : null;
  const prevResolved = prevStep ? resolveStep(prevStep) : null;
  const nextResolved = nextStep ? resolveStep(nextStep) : null;

  const handleNext = () => {
    // Mark current step complete if visualizer
    if (currentType === 'visualizer') {
      recordVisualizerVisit(currentId);
      if (user) {
        progressApi.visitVisualizer(currentId).catch(() => {});
      }
    }

    if (nextResolved) {
      navigate(`${nextResolved.link}?path=${matchedPath.id}&step=${currentStepIndex + 1}`);
    } else {
      navigate(`/learn/${matchedPath.id}`);
    }
  };

  const handlePrev = () => {
    if (prevResolved) {
      navigate(`${prevResolved.link}?path=${matchedPath.id}&step=${currentStepIndex - 1}`);
    }
  };

  return (
    <aside
      aria-label="Path navigation"
      className="relative z-30 rounded-xl border border-mint/20 bg-surface p-3 shadow-md"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        {/* Left: Path Back-Link & Step Switcher */}
        <div className="flex items-center gap-3 min-w-0">
          <Link
            to={`/learn/${matchedPath.id}`}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-line bg-canvas/60 text-[11px] font-mono text-muted hover:text-mint hover:border-mint/40 transition shrink-0"
            title={`Back to ${matchedPath.title}`}
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{matchedPath.title}</span>
          </Link>

          {/* Step dropdown button */}
          <div className="relative">
            <button
              onClick={() => setIsDropdownOpen(!isDropdownOpen)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-line bg-canvas/40 hover:bg-canvas text-left transition"
              aria-expanded={isDropdownOpen}
            >
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-mint animate-pulse" />
                <span className="text-[10px] font-mono text-mint font-semibold uppercase tracking-wider">
                  {`Step ${currentStepIndex + 1} of ${steps.length}`}
                </span>
              </div>
              <span className="text-xs font-semibold text-ink truncate max-w-[160px] sm:max-w-[240px]">
                {currentResolved?.title || currentId}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-muted shrink-0" />
            </button>

            {/* Dropdown list of all steps */}
            {isDropdownOpen && (
              <>
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setIsDropdownOpen(false)}
                />
                <div className="absolute left-0 mt-2 w-72 sm:w-84 max-h-80 overflow-y-auto rounded-xl border border-line bg-surface shadow-xl z-50 p-2 space-y-1">
                  <div className="px-2 py-1 text-[10px] font-mono uppercase tracking-[0.16em] text-muted border-b border-line pb-1.5">
                    {matchedPath.title} · Curriculum
                  </div>
                  {steps.map((step, idx) => {
                    const resolved = resolveStep(step);
                    const isStepActive = idx === currentStepIndex;
                    const isStepDone =
                      step.type === 'visualizer'
                        ? state.visitedVisualizers?.includes(step.id)
                        : step.type === 'problem'
                        ? state.progress[step.id] === 'Done'
                        : (state.quizzes[step.id] ?? 0) >= 70;
                    const IconComponent = STEP_ICONS[step.type] || Code2;

                    return (
                      <Link
                        key={`${step.type}-${step.id}-${idx}`}
                        to={`${resolved.link}?path=${matchedPath.id}&step=${idx}`}
                        onClick={() => setIsDropdownOpen(false)}
                        className={`flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs transition ${
                          isStepActive
                            ? 'bg-mint/15 text-mint font-semibold border border-mint/30'
                            : 'hover:bg-canvas text-ink'
                        }`}
                      >
                        <span className="font-mono text-[10px] text-muted w-4 shrink-0">
                          {idx + 1}.
                        </span>
                        <IconComponent className="w-3.5 h-3.5 shrink-0 text-muted" />
                        <span className="truncate flex-1">{resolved.title}</span>
                        {isStepDone && (
                          <CheckCircle2 className="w-3.5 h-3.5 text-mint shrink-0" />
                        )}
                      </Link>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        </div>

        {/* Right: Previous & Next / Complete & Continue CTA */}
        <div className="flex items-center gap-2 shrink-0">
          {prevResolved && (
            <button
              onClick={handlePrev}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-line bg-canvas/60 text-[11px] font-mono text-muted hover:text-ink hover:border-steel transition cursor-pointer"
              title={`Previous: ${prevResolved.title}`}
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span className="hidden md:inline">Prev</span>
            </button>
          )}

          <button
            onClick={handleNext}
            className="group flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-mint text-canvas font-semibold text-xs hover:bg-mint/90 transition shadow-sm cursor-pointer"
          >
            <span>
              {nextResolved
                ? `Next: ${nextResolved.title}`
                : 'Finish Path 🎉'}
            </span>
            <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>
      </div>
    </aside>
  );
};
