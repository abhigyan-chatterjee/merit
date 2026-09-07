import { useMemo } from 'react';

export function getTodayISO(): string {
  const now = new Date();
  return now.toISOString().split('T')[0];
}

export function useStreak(streakDates: string[], recordActivityDate: (date: string) => void) {
  const today = getTodayISO();

  const currentStreak = useMemo(() => {
    if (!streakDates || streakDates.length === 0) return 0;
    const uniqueSorted = Array.from(new Set(streakDates)).sort().reverse();
    let streak = 0;
    const d = new Date();

    // Check if today or yesterday is present
    const todayStr = d.toISOString().split('T')[0];
    const yesterdayDate = new Date(d);
    yesterdayDate.setDate(d.getDate() - 1);
    const yesterdayStr = yesterdayDate.toISOString().split('T')[0];

    const checkDate = uniqueSorted.includes(todayStr)
      ? new Date(d)
      : uniqueSorted.includes(yesterdayStr)
      ? yesterdayDate
      : null;

    if (!checkDate) return 0;

    while (true) {
      const iso = checkDate.toISOString().split('T')[0];
      if (uniqueSorted.includes(iso)) {
        streak++;
        checkDate.setDate(checkDate.getDate() - 1);
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
