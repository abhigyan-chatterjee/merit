import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { useProgress } from '../store/ProgressContext';
import { ProgressRing } from './ProgressRing';
import { TARGET_TIER_META, computeDaysToDrive, computePlacementReadiness } from '../utils/readiness';
import type { TargetTier } from '../store/ProgressContext';

interface PlacementReadinessPanelProps {
  summaryQuizScores?: Record<string, number>;
  summaryDueCount?: number;
}

export const PlacementReadinessPanel: React.FC<PlacementReadinessPanelProps> = ({
  summaryQuizScores,
  summaryDueCount,
}) => {
  const { state, currentStreak, dueTodayCount, targetTier, targetDriveDate, savePlacementTarget } = useProgress();

  const allQuizScores = { ...state.quizzes, ...(summaryQuizScores ?? {}) };
  const effectiveDue = summaryDueCount ?? dueTodayCount;
  const readiness = computePlacementReadiness({
    progress: state.progress,
    quizzes: allQuizScores,
    streakDays: currentStreak,
    dueTodayCount: effectiveDue,
    targetTier,
    targetDriveDate,
  });
  const days = computeDaysToDrive(targetDriveDate);
  const countdown =
    days === null ? 'Set drive date' : days === 0 ? 'Drive day!' : days > 0 ? `${days} days left` : 'Drive passed';

  const tiers: TargetTier[] = ['service', 'product', 'faang'];
  const pillars: Array<{ label: string; value: number; max: number }> = [
    { label: 'DSA Coverage', value: readiness.pillars.dsa, max: 45 },
    { label: 'Quizzes & CS', value: readiness.pillars.quizzes, max: 25 },
    { label: 'Mock Exams', value: readiness.pillars.exams, max: 20 },
    { label: 'Consistency', value: readiness.pillars.consistency, max: 10 },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
      <div className="p-5 rounded-2xl border border-line bg-surface space-y-5">
        <div className="flex items-center gap-5">
          <ProgressRing completed={readiness.score} total={100} size={96} strokeWidth={8} />
          <div className="space-y-1.5 min-w-0">
            <p className="text-[10px] font-mono uppercase tracking-[0.2em] text-muted">Placement Readiness</p>
            <p className="text-2xl font-bold font-mono text-ink tnum">
              {readiness.score}/100
            </p>
            <p className="text-[11px] text-muted">
              {readiness.band} · {TARGET_TIER_META[targetTier].label}
            </p>
            <p className="text-[11px] text-muted">
              {TARGET_TIER_META[targetTier].subtitle}
            </p>
          </div>
        </div>

        <div className="space-y-2.5">
          {pillars.map((p) => (
            <div key={p.label} className="space-y-1">
              <div className="flex items-center justify-between text-xs">
                <span className="text-ink font-medium">{p.label}</span>
                <span className="font-mono text-muted tnum">
                  {p.value}/{p.max}
                </span>
              </div>
              <span className="block h-1.5 rounded-full bg-line overflow-hidden">
                <span
                  className="block h-full bg-mint origin-left transition-transform"
                  style={{ transform: `scaleX(${p.max ? p.value / p.max : 0})` }}
                />
              </span>
            </div>
          ))}
        </div>

        <div className="space-y-2">
          <p className="text-[10px] font-mono uppercase tracking-[0.14em] text-muted">Target Tier</p>
          <div className="flex flex-wrap gap-2">
            {tiers.map((t) => (
              <button
                key={t}
                type="button"
                aria-pressed={targetTier === t}
                onClick={() => savePlacementTarget({ targetTier: t })}
                className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition cursor-pointer ${
                  targetTier === t
                    ? 'border-mint/60 bg-mint/10 text-mint'
                    : 'border-line bg-canvas text-muted hover:text-ink'
                }`}
              >
                {TARGET_TIER_META[t].label}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <p className="text-[10px] font-mono uppercase tracking-[0.14em] text-muted">Drive Countdown</p>
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="date"
              aria-label="Target placement drive date"
              value={targetDriveDate ?? ''}
              onChange={(e) => savePlacementTarget({ targetDriveDate: e.target.value || null })}
              className="px-3 py-1.5 rounded-lg bg-canvas border border-line text-xs text-ink font-mono focus:border-mint"
            />
            <span className="px-2 py-1 rounded-full text-[11px] font-mono border border-line bg-canvas text-ink">
              {countdown}
            </span>
            {targetDriveDate && (
              <button
                type="button"
                onClick={() => savePlacementTarget({ targetDriveDate: null })}
                className="px-2 py-1 rounded-lg border border-line text-[11px] font-mono text-muted hover:text-rose hover:border-rose/40 transition cursor-pointer"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="p-5 rounded-2xl border border-line bg-surface space-y-4">
        <h3 className="text-sm font-bold text-ink uppercase tracking-wider">Today&apos;s Focus</h3>
        <div className="space-y-3">
          {readiness.focusItems.map((item, idx) => (
            <Link
              key={item.id}
              to={item.link}
              className="group flex items-start gap-3 p-4 rounded-xl border border-line bg-canvas hover:border-mint/50 transition-colors"
            >
              <span className="font-mono text-xs text-muted tnum shrink-0 pt-0.5">
                {String(idx + 1).padStart(2, '0')}
              </span>
              <span className="min-w-0 flex-1 space-y-1">
                <span className="block text-sm font-semibold text-ink group-hover:text-mint transition-colors">
                  {item.title}
                </span>
                <span className="block text-xs text-muted">{item.detail}</span>
              </span>
              <span className="inline-flex items-center gap-1 text-xs font-mono text-muted group-hover:text-mint transition-colors shrink-0">
                {item.cta}
                <ArrowRight className="w-3.5 h-3.5" />
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
};
