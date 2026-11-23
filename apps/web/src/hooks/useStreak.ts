import { useEffect, useMemo, useState } from 'react';

/**
 * Returns the YYYY-MM-DD day key in UTC. Every day-keyed record
 * (streak days, daily goals, activity rows) uses this so a session
 * logged anywhere in the world lands on the same day for every
 * client and for the server.
 */
export function getUTCDateString(d: Date = new Date()): string {
  const year = d.getUTCFullYear();
  const month = String(d.getUTCMonth() + 1).padStart(2, '0');
  const day = String(d.getUTCDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

/** How often a mounted tab re-checks whether the UTC day has rolled over. */
const DAY_TICK_MS = 60_000;

export function useStreak(streakDates: string[], recordActivityDate: (date: string) => void) {
  // The day key is state, not a value computed at render: a tab left open
  // across UTC midnight would otherwise keep crediting activity to yesterday.
  const [today, setToday] = useState<string>(() => getUTCDateString());

  useEffect(() => {
    const refreshDay = () => {
      setToday((prev) => {
        const next = getUTCDateString();
        return next === prev ? prev : next;
      });
    };
    const onVisibility = () => {
      if (!document.hidden) refreshDay();
    };
    const timer = setInterval(refreshDay, DAY_TICK_MS);
    document.addEventListener('visibilitychange', onVisibility);
    window.addEventListener('focus', refreshDay);
    return () => {
      clearInterval(timer);
      document.removeEventListener('visibilitychange', onVisibility);
      window.removeEventListener('focus', refreshDay);
    };
  }, []);

  const currentStreak = useMemo(() => {
    if (!streakDates || streakDates.length === 0) return 0;
    const uniqueSorted = Array.from(new Set(streakDates)).sort().reverse();

    // Derived from the tracked day key (not the wall clock) so a rollover
    // recomputes the streak against the same day everything else uses.
    const [year, month, day] = today.split('-').map(Number);
    const yesterdayDate = new Date(Date.UTC(year, month - 1, day - 1));
    const yesterdayStr = getUTCDateString(yesterdayDate);

    const checkDate = uniqueSorted.includes(today)
      ? new Date(Date.UTC(year, month - 1, day))
      : uniqueSorted.includes(yesterdayStr)
      ? yesterdayDate
      : null;

    if (!checkDate) return 0;

    let streak = 0;
    while (true) {
      const dayStr = getUTCDateString(checkDate);
      if (uniqueSorted.includes(dayStr)) {
        streak++;
        checkDate.setUTCDate(checkDate.getUTCDate() - 1);
      } else {
        break;
      }
    }
    return streak;
  }, [streakDates, today]);

  const markTodayActive = () => {
    if (!streakDates.includes(today)) {
      recordActivityDate(today);
    }
  };

  return { currentStreak, markTodayActive, today };
}
