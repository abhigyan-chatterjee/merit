import React, { useMemo } from 'react';
import { Flame } from 'lucide-react';

interface StreakHeatmapProps {
  streakDates: string[];
  currentStreak: number;
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const WEEKS = 18;

export const StreakHeatmap: React.FC<StreakHeatmapProps> = ({ streakDates, currentStreak }) => {
  const { weeks, monthMarks, activeCount } = useMemo(() => {
    const set = new Set(streakDates);
    const today = new Date();
    // Anchor to the end of the current week so columns align to Sun..Sat
    const anchor = new Date(today);
    anchor.setDate(today.getDate() + (6 - today.getDay()));

    const grid: { date: string; level: number; future: boolean }[][] = [];
    const marks: { col: number; label: string }[] = [];
    let lastMonth = -1;
    let count = 0;

    for (let w = WEEKS - 1; w >= 0; w--) {
      const col: { date: string; level: number; future: boolean }[] = [];
      for (let d = 6; d >= 0; d--) {
        const offset = w * 7 + d;
        const dt = new Date(anchor);
        dt.setDate(anchor.getDate() - offset);
        const iso = dt.toISOString().split('T')[0];
        const active = set.has(iso);
        if (active) count++;
        col.unshift({
          date: iso,
          level: active ? ((dt.getDate() % 3) + 1) : 0,
          future: dt > today
        });
      }
      const colIndex = WEEKS - 1 - w;
      const firstOfCol = new Date(col[0].date);
      if (firstOfCol.getMonth() !== lastMonth) {
        lastMonth = firstOfCol.getMonth();
        marks.push({ col: colIndex, label: MONTHS[lastMonth] });
      }
      grid.push(col);
    }
    return { weeks: grid, monthMarks: marks, activeCount: count };
  }, [streakDates]);

  const cellClass = (level: number, future: boolean) => {
    if (future) return 'bg-transparent border-line/40';
    switch (level) {
      case 1: return 'bg-mint/30 border-mint/30';
      case 2: return 'bg-mint/60 border-mint/50';
      case 3: return 'bg-mint border-mint';
      default: return 'bg-canvas border-line';
    }
  };

  return (
    <div className="rounded-xl border border-line bg-surface">
      {/* header rail — single line, no wrapping: the bottom border must
          never slice through badges, so height grows instead of clipping */}
      <div className="flex items-center justify-between gap-3 px-4 py-2 min-h-11 border-b border-line whitespace-nowrap overflow-x-auto">
        <span className="inline-flex shrink-0 items-center gap-2 text-[10px] font-mono uppercase tracking-[0.16em] text-muted">
          <span className="w-1 h-1 rounded-full bg-mint" />
          Activity · last {WEEKS} weeks
        </span>
        <div className="flex shrink-0 items-center gap-4 font-mono text-[11px]">
          <span className="text-muted">
            <span className="text-ink font-bold tnum">{activeCount}</span> active days
          </span>
          <span title={`${currentStreak} day streak`} className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded border border-mint/40 bg-mint/10 text-mint">
            <Flame className="w-3 h-3" />
            <span className="font-bold tnum">{currentStreak}</span>
          </span>
        </div>
      </div>

      <div className="flex justify-center p-4">
        <div>
          {/* month axis */}
          <div className="flex gap-[3px] ml-8 mb-1.5 h-3">
            {weeks.map((_, i) => {
              const mark = monthMarks.find((m) => m.col === i);
              return (
                <div key={i} className="w-3 shrink-0">
                  {mark && (
                    <span className="text-[9px] font-mono text-muted whitespace-nowrap">
                      {mark.label}
                    </span>
                  )}
                </div>
              );
            })}
          </div>

          <div className="flex gap-[3px]">
            {/* weekday axis */}
            <div className="flex flex-col gap-[3px] w-8 pr-1.5 shrink-0">
              {['', 'Mon', '', 'Wed', '', 'Fri', ''].map((d, i) => (
                <div key={i} className="h-3 flex items-center justify-end">
                  <span className="text-[9px] font-mono text-muted leading-none">{d}</span>
                </div>
              ))}
            </div>

            {weeks.map((week, wIdx) => (
              <div key={wIdx} className="flex flex-col gap-[3px] shrink-0">
                {week.map((day) => (
                  <div
                    key={day.date}
                    title={
                      day.future
                        ? day.date
                        : `${day.date} — ${day.level > 0 ? 'active session' : 'no activity'}`
                    }
                    className={`w-3 h-3 rounded-[2px] border transition-transform duration-150 hover:scale-[1.35] ${cellClass(
                      day.level,
                      day.future
                    )}`}
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* legend rail */}
      <div className="flex items-center justify-end gap-1.5 px-4 py-2 border-t border-line text-[10px] font-mono text-muted">
        <span className="mr-1">Less</span>
        <span className="w-3 h-3 rounded-[2px] border border-line bg-canvas" />
        <span className="w-3 h-3 rounded-[2px] border border-mint/30 bg-mint/30" />
        <span className="w-3 h-3 rounded-[2px] border border-mint/50 bg-mint/60" />
        <span className="w-3 h-3 rounded-[2px] border border-mint bg-mint" />
        <span className="ml-1">More</span>
      </div>
    </div>
  );
};
