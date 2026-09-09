import React, { useState, useEffect, useRef } from 'react';
import { Target, Plus, X, CheckSquare, Square, Pin, PinOff } from 'lucide-react';
import { useProgress, DAILY_GOAL_PRESETS } from '../store/ProgressContext';
import type { DailyGoal } from '../store/ProgressContext';
import { useAuth } from '../store/AuthContext';

export const DailyGoalMenu: React.FC = () => {
  const { user } = useAuth();
  const {
    dailyGoal,
    dailyGoalProgressToday,
    isDailyGoalDone,
    setDailyGoal,
    clearDailyGoal,
    unpinDailyGoal,
    toggleDailyGoal,
  } = useProgress();
  const [open, setOpen] = useState(false);
  const [customLabel, setCustomLabel] = useState('');
  const [pinIt, setPinIt] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('mousedown', onDown);
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('mousedown', onDown);
      window.removeEventListener('keydown', onKey);
    };
  }, [open ]);

  const progressText = dailyGoal
    ? dailyGoal.kind === 'problems'
      ? `${Math.min(dailyGoalProgressToday, dailyGoal.target)}/${dailyGoal.target} today`
      : dailyGoal.kind === 'quiz-score'
      ? `${dailyGoal.target}% quiz`
      : 'manual'
    : 'Set goal';

  const choose = (goal: DailyGoal) => {
    setDailyGoal(goal, { permanent: pinIt && !!user });
    setPinIt(false);
    setOpen(false);
  };

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        title={dailyGoal ? `Daily goal: ${dailyGoal.label}` : 'Set a daily goal'}
        aria-label="Daily goal"
        aria-expanded={open}
        className={`inline-flex items-center gap-1.5 px-2.5 py-2 rounded-lg border text-xs font-mono transition cursor-pointer ${
          isDailyGoalDone
            ? 'border-mint/50 bg-mint/10 text-mint'
            : dailyGoal
            ? 'border-amber/50 bg-amber/10 text-amber'
            : 'border-line bg-surface text-muted hover:text-ink hover:border-steel'
        }`}
      >
        <Target className="w-3.5 h-3.5" />
        <span className="hidden sm:inline max-w-[140px] truncate">{progressText}</span>
        {dailyGoal?.permanent && <Pin className="w-3 h-3" aria-label="Permanent goal" />}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-72 rounded-xl border border-line bg-surface shadow-2xl p-3 space-y-2 z-50">
          {dailyGoal ? (
            <div className="space-y-2 pb-2 border-b border-line">
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs font-semibold text-ink truncate">{dailyGoal.label}</p>
                <button
                  onClick={toggleDailyGoal}
                  aria-pressed={isDailyGoalDone}
                  className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg border text-[11px] transition cursor-pointer shrink-0 ${
                    isDailyGoalDone
                      ? 'border-mint/50 bg-mint/10 text-mint'
                      : 'border-line bg-canvas text-muted hover:text-ink'
                  }`}
                >
                  {isDailyGoalDone ? <CheckSquare className="w-3.5 h-3.5" /> : <Square className="w-3.5 h-3.5" />}
                  {isDailyGoalDone ? 'Done' : 'Mark done'}
                </button>
              </div>
              {dailyGoal.permanent ? (
                <button
                  onClick={() => {
                    unpinDailyGoal();
                    setOpen(false);
                  }}
                  className="inline-flex items-center gap-1 text-[11px] font-mono text-muted hover:text-rose transition cursor-pointer"
                >
                  <PinOff className="w-3 h-3" /> Unpin permanent goal
                </button>
              ) : (
                <button
                  onClick={() => {
                    clearDailyGoal();
                    setOpen(false);
                  }}
                  className="inline-flex items-center gap-1 text-[11px] font-mono text-muted hover:text-rose transition cursor-pointer"
                >
                  <X className="w-3 h-3" /> Clear goal
                </button>
              )}
            </div>
          ) : (
            <p className="text-xs text-muted pb-1">No goal yet — pick one to track today.</p>
          )}

          <div className="space-y-1.5">
            {DAILY_GOAL_PRESETS.map((preset) => (
              <button
                key={preset.label}
                onClick={() => choose(preset)}
                className="w-full text-left px-3 py-2 rounded-lg border border-line bg-canvas text-xs text-ink hover:border-mint transition cursor-pointer"
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
              placeholder="Custom, e.g. Revise DP 20 min"
              aria-label="Custom daily goal"
              className="flex-1 min-w-0 px-3 py-2 rounded-lg bg-canvas border border-line text-xs text-ink placeholder-muted/60 focus:outline-none focus:border-mint"
            />
            <button
              type="submit"
              aria-label="Add custom goal"
              className="p-2 rounded-lg bg-mint text-canvas hover:brightness-110 transition cursor-pointer shrink-0"
            >
              <Plus className="w-3.5 h-3.5" />
            </button>
          </form>

          {user ? (
            <label className="flex items-center gap-2 text-[11px] font-mono text-muted cursor-pointer select-none">
              <input
                type="checkbox"
                checked={pinIt}
                onChange={(e) => setPinIt(e.target.checked)}
                className="accent-emerald-500"
              />
              Keep as my permanent goal
            </label>
          ) : (
            <p className="text-[10px] font-mono text-muted">Sign in to keep a permanent goal.</p>
          )}
        </div>
      )}
    </div>
  );
};
