import { useMemo } from 'react';

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

export function useStreak(streakDates: string[], recordActivityDate: (date: string) => void) {
  const today = getUTCDateString();

  const currentStreak = useMemo(() => {
    if (!streakDates || streakDates.length === 0) return 0;
    const uniqueSorted = Array.from(new Set(streakDates)).sort().reverse();
    let streak = 0;
    const d = new Date();

    const todayStr = getUTCDateString(d);
    const yesterdayDate = new Date(
      Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate() - 1)
    );
    const yesterdayStr = getUTCDateString(yesterdayDate);

    const checkDate = uniqueSorted.includes(todayStr)
      ? new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()))
      : uniqueSorted.includes(yesterdayStr)
      ? yesterdayDate
      : null;

    if (!checkDate) return 0;

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
  }, [streakDates]);

  const markTodayActive = () => {
    if (!streakDates.includes(today)) {
      recordActivityDate(today);
    }
  };

  return { currentStreak, markTodayActive, today };
}
