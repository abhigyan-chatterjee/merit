import React, { useState } from 'react';
import { CheckSquare, Square, Target, Plus, X } from 'lucide-react';
import { useProgress, DAILY_GOAL_PRESETS } from '../store/ProgressContext';
import type { DailyGoal } from '../store/ProgressContext';

export const DailyGoalCard: React.FC = () => {
  const { dailyGoal, dailyGoalProgressToday, isDailyGoalDone, setDailyGoal, toggleDailyGoal } =
    useProgress();
  const [editing, setEditing] = useState(false);
  const [customLabel, setCustomLabel] = useState('');

  const progressText = dailyGoal
    ? dailyGoal.kind === 'problems'
      ? `${Math.min(dailyGoalProgressToday, dailyGoal.target)}/${dailyGoal.target} solved today`
      : dailyGoal.kind === 'quiz-score'
      ? `target ${dailyGoal.target}% in one quiz`
      : 'manual check-off'
    : 'no goal set';

  const pct =
    dailyGoal && dailyGoal.kind !== 'custom'
      ? Math.min(100, Math.round((dailyGoalProgressToday / Math.max(1, dailyGoal.target)) * 100))
      : isDailyGoalDone
      ? 100
      : 0;

  const choose = (goal: DailyGoal) => {
    setDailyGoal(goal);
    setEditing(false);
  };

  return (
    <div className="rounded-xl border border-line bg-surface p-4 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <span className="inline-flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-[0.16em] text-muted">
          <Target className="w-3.5 h-3.5 text-amber" />
          Daily goal
        </span>
        <button
          onClick={() => setEditing((e) => !e)}
          className="text-[11px] font-mono text-muted hover:text-mint transition cursor-pointer"
          aria-expanded={editing}
        >
          {dailyGoal ? 'Change' : 'Set goal'}
        </button>
      </div>

      {dailyGoal ? (
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs font-semibold text-ink truncate">{dailyGoal.label}</p>
            <button
              onClick={toggleDailyGoal}
              aria-pressed={isDailyGoalDone}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[11px] font-medium transition cursor-pointer shrink-0 ${
                isDailyGoalDone
                  ? 'border-mint/50 bg-mint/10 text-mint'
                  : 'border-line bg-canvas text-muted hover:text-ink hover:border-steel'
              }`}
            >
              {isDailyGoalDone ? <CheckSquare className="w-3.5 h-3.5" /> : <Square className="w-3.5 h-3.5" />}
              {isDailyGoalDone ? 'Done' : 'Mark done'}
            </button>
          </div>
          <div className="flex items-center gap-2">
            <span className="flex-1 h-1.5 rounded-full bg-line overflow-hidden">
              <span
                className={`block h-full transition-all duration-300 ${isDailyGoalDone ? 'bg-mint' : 'bg-amber'}`}
                style={{ width: `${pct}%` }}
              />
            </span>
            <span className="text-[10px] font-mono text-muted tnum shrink-0">{progressText}</span>
          </div>
        </div>
      ) : (
        <p className="text-xs text-muted">
          No goal yet — set one to track today&apos;s practice target.
        </p>
      )}

      {editing && (
        <div className="space-y-2 pt-1 border-t border-line">
          <div className="grid grid-cols-1 gap-1.5 pt-2">
            {DAILY_GOAL_PRESETS.map((preset) => (
              <button
                key={preset.label}
                onClick={() => choose(preset)}
                className="text-left px-3 py-2 rounded-lg border border-line bg-canvas text-xs text-ink hover:border-mint transition cursor-pointer"
              >
                {preset.label}
              </button>
            ))}
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const label = customLabel.trim();
              if (!label) return;
              choose({ kind: 'custom', label, target: 1 });
              setCustomLabel('');
            }}
            className="flex items-center gap-2"
          >
            <input
              value={customLabel}
              onChange={(e) => setCustomLabel(e.target.value)}
              placeholder="Custom goal, e.g. Revise DP notes 20 min"
              aria-label="Custom daily goal"
              className="flex-1 px-3 py-2 rounded-lg bg-canvas border border-line text-xs text-ink placeholder-muted/60 focus:outline-none focus:border-mint"
            />
            <button
              type="submit"
              aria-label="Add custom goal"
              className="p-2 rounded-lg bg-mint text-canvas hover:brightness-110 transition cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </form>
          {dailyGoal && (
            <button
              onClick={() => {
                setDailyGoal(null);
                setEditing(false);
              }}
              className="inline-flex items-center gap-1 text-[11px] font-mono text-muted hover:text-rose transition cursor-pointer"
            >
              <X className="w-3 h-3" /> Clear goal
            </button>
          )}
        </div>
      )}
    </div>
  );
};
